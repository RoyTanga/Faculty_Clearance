from flask import Flask, request, render_template, redirect, url_for
import os
import smtplib
from email.mime.text import MIMEText
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
import PyPDF2

app = Flask(__name__)

# Load the pre-trained model and vectorizer (assume they're already trained)
model = joblib.load('document_classifier.pkl')
vectorizer = joblib.load('tfidf_vectorizer.pkl')

# Directory to save uploaded files
UPLOAD_FOLDER = './uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Required documents
required_documents = ['Grade Clearance', 'Clearance from Chair']

# Helper function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in range(len(reader.pages)):
            text += reader.pages[page].extract_text()
    return text

# Helper function to categorize a document
def parse_and_categorize(document_text):
    vectorized_text = vectorizer.transform([document_text])
    prediction = model.predict(vectorized_text)[0]
    return prediction

# Function to send email notification
def send_email_notification(faculty_email, missing_docs):
    msg = MIMEText(f'The following documents are missing: {", ".join(missing_docs)}. Please submit them.')
    msg['Subject'] = 'Missing Clearance Documents'
    msg['From'] = 'rtanga@usiu.ac.ke'
    msg['To'] = faculty_email

    with smtplib.SMTP('smtp.usiu.ac.ke') as server:
        server.login('rtanga@usiu.ac.ke', '666080.rst')
        server.sendmail('rtanga@usiu.ac.ke', faculty_email, msg.as_string())

# Main route for document upload
@app.route('/', methods=['GET', 'POST'])
def upload_documents():
    if request.method == 'POST':
        uploaded_files = request.files.getlist('files[]')
        faculty_email = request.form.get('email')
        submitted_documents = []

        for file in uploaded_files:
            if file.filename != '':
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(filepath)

                # Extract text from the uploaded PDF
                document_text = extract_text_from_pdf(filepath)
                
                # Categorize the document
                category = parse_and_categorize(document_text)
                submitted_documents.append(category)

        # Check for missing documents
        missing_documents = set(required_documents) - set(submitted_documents)

        if missing_documents:
            send_email_notification(faculty_email, missing_documents)
            return f"Missing documents detected: {', '.join(missing_documents)}. An email has been sent to {faculty_email}."

        return "All required documents are submitted. No missing documents."

    return render_template('upload.html')

if __name__ == '__main__':
    # Ensure the upload folder exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
