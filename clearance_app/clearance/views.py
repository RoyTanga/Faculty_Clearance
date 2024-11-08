import json
import os
import shutil
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import DocumentForm, PredictionForm, FacultySignUpForm, AdminSignUpForm, DocumentUploadForm, ClearanceSetForm
from .models import Document, User, ClearanceSet
from .clearance_classifier import ClearanceClassifier
import logging
from docx import Document as DocxDocument
from django.urls import reverse
from .clearance_predictor import ClearancePredictor
from datetime import datetime
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db import IntegrityError
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .utils import send_clearance_status_email

logging.basicConfig(level=logging.INFO)

# Initialize the classifier
model_dir = os.path.join(os.path.dirname(__file__), 'models')
csv_path = '/Users/roytanga/Desktop/Work APT3065A/Clearance Prof/clearance_dataset.csv'  # Update this path

# Delete existing models
if os.path.exists(model_dir):
    logging.info(f"Deleting existing model directory: {model_dir}")
    shutil.rmtree(model_dir)

logging.info(f"Initializing classifier with model_dir: {model_dir} and csv_path: {csv_path}")
classifier = ClearanceClassifier(model_dir, csv_path)
logging.info(f"Classifier initialized. Is fitted: {classifier.is_fitted}")

def classify_clearance(request):
    if request.method == 'POST':
        try:
            # Parse the JSON data from the request body
            clearances = json.loads(request.body)

            # Validate the structure of the incoming JSON data
            clearances_dict = {
                'Admin_Clearance': clearances.get('Admin_Clearance', False),
                'Research_Clearance': clearances.get('Research_Clearance', False),
                'Grade_Submission': clearances.get('Grade_Submission', False),
                'Library_Clearance': clearances.get('Library_Clearance', False),
                'Equipment_Returned': clearances.get('Equipment_Returned', False)
            }

            # Pass the extracted data to the classifier
            result = classifier.classify_faculty(clearances_dict)

            # Return the classification result
            return JsonResponse({'predicted_clearances': list(result)})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)

    return JsonResponse({'error': 'Only POST requests allowed'}, status=405)

def upload_document(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save()
            messages.success(request, 'Document uploaded successfully.')
            return redirect('document_list')
    else:
        form = DocumentForm()
    return render(request, 'clearance/upload.html', {'form': form})

def document_list(request):
    documents = Document.objects.all().order_by('-uploaded_at')
    prediction_form = PredictionForm()
    
    if request.method == 'POST':
        prediction_form = PredictionForm(request.POST)
        if prediction_form.is_valid():
            unpredicted_documents = documents.filter(clearance_status='')
            for document in unpredicted_documents:
                logging.info(f"Processing document: {document.file.name}")
                clearances = process_document(document.file.path)
                logging.info(f"Clearances detected: {clearances}")
                logging.info(f"Classifier fitted: {classifier.is_fitted}")
                predicted_clearances = classifier.classify_faculty(clearances)
                logging.info(f"Predicted clearances: {predicted_clearances}")
                document.clearance_status = ', '.join(predicted_clearances) if predicted_clearances else 'No clearances predicted'
                document.predicted_at = timezone.now()
                document.save()
            messages.success(request, f'Predictions completed for {unpredicted_documents.count()} documents.')
            return redirect('document_list')
    
    return render(request, 'clearance/document_list.html', {
        'documents': documents,
        'prediction_form': prediction_form
    })

import re
from docx import Document as DocxDocument

def process_document(file_path):
    clearances = {
        'Admin_Clearance': False,
        'Research_Clearance': False,
        'Grade_Submission': False,
        'Library_Clearance': False,
        'Equipment_Returned': False
    }
    
    keywords = {
        'Admin_Clearance': ['administrative clearance', 'admin approved', 'administration clear'],
        'Research_Clearance': ['research clearance', 'research approved', 'research obligations met'],
        'Grade_Submission': ['grades submitted', 'grade clearance', 'academic records clear'],
        'Library_Clearance': ['library clearance', 'library dues cleared', 'no outstanding library fees'],
        'Equipment_Returned': ['equipment returned', 'no outstanding equipment', 'lab clearance']
    }
    
    try:
        if file_path.lower().endswith('.docx'):
            doc = DocxDocument(file_path)
            content = ' '.join([paragraph.text for paragraph in doc.paragraphs])
        else:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
        
        content = content.lower()
        
        for clearance_type, keyword_list in keywords.items():
            for keyword in keyword_list:
                if keyword in content:
                    clearances[clearance_type] = True
                    print(f"Keyword found: {keyword} for {clearance_type}")
                    break
        
        print(f"Document content length: {len(content)} characters")
        print(f"Detected clearances: {clearances}")
        
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
    
    return clearances

def faculty_signup(request):
    if request.method == 'POST':
        form = FacultySignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('faculty_dashboard')  # Make sure you have this URL pattern defined
    else:
        form = FacultySignUpForm()
    return render(request, 'clearance/faculty_signup.html', {'form': form})

def admin_signup(request):
    if request.method == 'POST':
        form = AdminSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('admin_dashboard')
    else:
        form = AdminSignUpForm()
    return render(request, 'clearance/admin_signup.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.is_faculty)
def faculty_dashboard(request):
    clearance_sets = ClearanceSet.objects.filter(faculty=request.user).order_by('-created_at')
    
    # Calculate statistics
    total_documents = Document.objects.filter(clearance_set__faculty=request.user).count()
    approved_documents = Document.objects.filter(
        clearance_set__faculty=request.user,
        predicted_status='APPROVED'
    ).count()
    pending_documents = Document.objects.filter(
        clearance_set__faculty=request.user,
        predicted_status='PENDING'
    ).count()
    
    context = {
        'clearance_sets': clearance_sets,
        'clearance_types': dict(Document.CLEARANCE_TYPES),
        'total_documents': total_documents,
        'approved_documents': approved_documents,
        'pending_documents': pending_documents,
    }
    return render(request, 'clearance/faculty_dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.is_admin)
def admin_dashboard(request):
    clearance_sets = ClearanceSet.objects.all().order_by('-created_at')
    return render(request, 'clearance/admin_dashboard.html', {'clearance_sets': clearance_sets})

class UploadDocumentView(LoginRequiredMixin, FormView):
    form_class = DocumentUploadForm
    template_name = 'clearance/upload_document.html'
    success_url = reverse_lazy('faculty_dashboard')

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        files = request.FILES.getlist('files')
        if form.is_valid():
            clearance_set, created = ClearanceSet.objects.get_or_create(faculty=request.user)
            clearance_type = form.cleaned_data['clearance_type']
            
            for file in files:
                document = Document.objects.create(
                    clearance_set=clearance_set,
                    clearance_type=clearance_type,
                    file=file,
                    file_name=file.name
                )

                logger.info(f"Document uploaded: id={document.id}, type={document.clearance_type}, name={document.file_name}")

                try:
                    predictor = ClearancePredictor()
                    predicted_status = predictor.predict(document)
                    document.predicted_status = predicted_status
                    document.save()
                    messages.success(request, f"Prediction made for {file.name}: {predicted_status}")
                    logger.info(f"Prediction made for document {document.id}: {predicted_status}")
                except Exception as e:
                    messages.error(request, f"Error in prediction for {file.name}: {str(e)}")
                    logger.error(f"Error in prediction for document {document.id}: {str(e)}", exc_info=True)

            return self.form_valid(form)
        else:
            return self.form_invalid(form)

@login_required
@user_passes_test(lambda u: u.is_admin)
def predict_clearances(request, set_id):
    clearance_set = ClearanceSet.objects.get(id=set_id)
    classifier = ClearanceClassifier()  # Initialize your classifier here
    
    for document in clearance_set.documents.all():
        # Process the document and get clearances
        clearances = process_document(document.file.path)
        
        # Predict clearance
        predicted_clearance = classifier.classify_faculty(clearances)
        
        # Update document
        document.clearance_status = ', '.join(predicted_clearance) if predicted_clearance else 'No clearances predicted'
        document.predicted_at = timezone.now()
        document.save()
    
    clearance_set.is_complete = True
    clearance_set.save()
    
    return redirect('admin_dashboard')

def custom_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect(reverse('admin:index'))  # Redirect to admin dashboard
            elif user.is_faculty:
                return redirect('faculty_dashboard')
            elif user.is_admin:
                return redirect('admin_dashboard')
            else:
                return redirect('home')  # or any default dashboard
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'clearance/login.html')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def super_dashboard(request):
    # Your superuser dashboard logic here   
    return render(request, 'clearance/super_dashboard.html')

def custom_logout(request):
    logout(request)
    return redirect('login')  # or wherever you want to redirect after logout

logger = logging.getLogger(__name__)

@login_required
def upload_document(request):
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Get the current academic year
            current_year = timezone.now().year
            academic_year = f"{current_year}-{current_year+1}"

            # Try to get the existing ClearanceSet or create a new one
            try:
                clearance_set = ClearanceSet.objects.get(
                    faculty=request.user,
                    academic_year=academic_year
                )
            except ClearanceSet.DoesNotExist:
                clearance_set = ClearanceSet.objects.create(
                    faculty=request.user,
                    academic_year=academic_year
                )

            clearance_type = form.cleaned_data['clearance_type']
            files = form.cleaned_data['files']

            for file in files:
                document = Document.objects.create(
                    clearance_set=clearance_set,
                    clearance_type=clearance_type,
                    file=file,
                    file_name=file.name
                )

                logger.info(f"Document uploaded: id={document.id}, type={document.clearance_type}, name={document.file_name}")

                try:
                    predictor = ClearancePredictor()
                    predicted_status = predictor.predict(document)
                    document.predicted_status = predicted_status
                    document.save()
                    messages.success(request, f"Prediction made for {file.name}: {predicted_status}")
                    logger.info(f"Prediction made for document {document.id}: {predicted_status}")
                except Exception as e:
                    messages.error(request, f"Error in prediction for {file.name}: {str(e)}")
                    logger.error(f"Error in prediction for document {document.id}: {str(e)}", exc_info=True)

            return redirect('faculty_dashboard')
    else:
        form = DocumentUploadForm()
    return render(request, 'clearance/upload_document.html', {'form': form})

@login_required
def document_detail(request, pk):
    document = get_object_or_404(Document, pk=pk)
    return render(request, 'clearance/document_detail.html', {'document': document})

@login_required
def create_new_set(request):
    if request.method == 'POST':
        form = ClearanceSetForm(request.POST)
        if form.is_valid():
            current_year = timezone.now().year
            academic_year = f"{current_year}-{current_year+1}"
            
            new_set = form.save(commit=False)
            new_set.faculty = request.user
            new_set.academic_year = academic_year
            new_set.save()
            
            logger.info(f"New clearance set '{new_set.name}' created for user {request.user.username}")
            messages.success(request, f"New clearance set '{new_set.name}' created successfully.")
            return redirect('faculty_dashboard')
    else:
        form = ClearanceSetForm()
    
    return render(request, 'clearance/create_new_set.html', {'form': form})

@login_required
def upload_document(request, set_id, clearance_type):
    clearance_set = get_object_or_404(ClearanceSet, id=set_id, faculty=request.user)
    document = Document.objects.filter(clearance_set=clearance_set, clearance_type=clearance_type).first()

    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            new_document = form.save(commit=False)
            new_document.clearance_set = clearance_set
            new_document.clearance_type = clearance_type
            new_document.save()
            messages.success(request, 'Document uploaded successfully.')
            return redirect('faculty_dashboard')
    else:
        form = DocumentUploadForm(instance=document)

    context = {
        'form': form,
        'clearance_set': clearance_set,
        'clearance_type': dict(Document.CLEARANCE_TYPES)[clearance_type],
    }
    return render(request, 'clearance/upload_document.html', context)

@require_POST
@login_required
def predict_all(request):
    if request.method == 'POST':
        set_id = request.POST.get('set_id')
        clearance_set = get_object_or_404(ClearanceSet, id=set_id, faculty=request.user)
        predictor = ClearancePredictor()
        
        # Get all documents for this set
        documents = Document.objects.filter(clearance_set=clearance_set)
        
        for document in documents:
            # Predict status
            predicted_status = predictor.predict(document)
            document.predicted_status = predicted_status
            document.save()
            
            # Send email notification
            send_clearance_status_email(document)
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)

