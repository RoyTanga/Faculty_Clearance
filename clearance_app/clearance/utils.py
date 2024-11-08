from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging
from django.contrib.staticfiles.storage import staticfiles_storage
from django.contrib.sites.shortcuts import get_current_site

logger = logging.getLogger(__name__)

def send_clearance_status_email(document, request=None):
    """Send email notification about document clearance status."""
    try:
        # Get the faculty email
        faculty_email = document.clearance_set.faculty.email
        
        # Get the site domain for absolute URLs
        if request:
            current_site = get_current_site(request)
            domain = current_site.domain
        else:
            domain = 'example.com'  # fallback domain
        
        # Create absolute URL for logo
        email_logo_url = f'https://{domain}{staticfiles_storage.url("clearance/images/email-logo.png")}'
        
        # Define status colors for HTML email
        status_colors = {
            'APPROVED': '#28a745',  # Green
            'REJECTED': '#dc3545',  # Red
            'PENDING': '#ffc107'    # Yellow
        }

        # Prepare context for email template
        context = {
            'faculty_name': document.clearance_set.faculty.get_full_name() or document.clearance_set.faculty.username,
            'clearance_type': document.get_clearance_type_display(),
            'status': document.clearance_status,
            'status_color': status_colors.get(document.clearance_status, '#6c757d'),
            'predicted_status': document.predicted_status,
            'set_name': document.clearance_set.name,
            'academic_year': document.clearance_set.academic_year,
            'file_name': document.file_name,
            'uploaded_at': document.uploaded_at,
            'email_logo_url': email_logo_url,
        }

        # Render email templates
        html_message = render_to_string('clearance/email/status_notification.html', context)
        plain_message = render_to_string('clearance/email/status_notification.txt', context)

        # Send email
        send_mail(
            subject=f'Clearance Status Update - {document.get_clearance_type_display()}',
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[faculty_email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Status email sent successfully for document {document.id} to {faculty_email}")
        return True

    except Exception as e:
        logger.error(f"Error sending status email for document {document.id}: {str(e)}")
        return False 