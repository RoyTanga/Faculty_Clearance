import re
from datetime import datetime
import logging
from docx import Document as DocxDocument
from django.utils import timezone
import PyPDF2
import docx
import chardet

logger = logging.getLogger(__name__)

class ClearancePredictor:
    def __init__(self):
        self.keywords = {
            'ADMIN': ['administrative clearance', 'admin approved', 'administration clear'],
            'ACADEMIC': ['grades submitted', 'grade clearance', 'academic records clear'],
            'FINANCIAL': ['financial clearance', 'fees paid', 'no outstanding balance'],
            'LIBRARY': ['library clearance', 'library dues cleared', 'no outstanding library fees'],
            'RESEARCH': ['research clearance', 'research approved', 'research obligations met'],
            'EQUIPMENT': ['equipment returned', 'no outstanding equipment', 'lab clearance']
        }

    def predict(self, document):
        logger.info(f"Starting prediction for document {document.id}")
        
        clearances = self.process_document(document.file.path)
        
        clearance_key = document.clearance_type
        
        if clearance_key in clearances and clearances[clearance_key]:
            predicted_status = 'APPROVED'
        else:
            predicted_status = 'PENDING'
        
        logger.info(f"Predicted status: {predicted_status}")

        # Save the predicted status to the document
        document.predicted_status = predicted_status
        document.predicted_at = timezone.now()
        document.save()

        logger.info(f"Saved prediction for document {document.id}: {predicted_status}")

        return predicted_status

    def process_document(self, file_path):
        clearances = {key: False for key in self.keywords.keys()}
        
        try:
            if file_path.lower().endswith('.pdf'):
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    content = ""
                    for page in pdf_reader.pages:
                        content += page.extract_text()
            elif file_path.lower().endswith('.docx'):
                doc = DocxDocument(file_path)
                content = ' '.join([paragraph.text for paragraph in doc.paragraphs])
            else:
                with open(file_path, 'rb') as file:
                    raw_data = file.read()
                    result = chardet.detect(raw_data)
                    content = raw_data.decode(result['encoding'])
            
            content = content.lower()
            
            for clearance_type, keyword_list in self.keywords.items():
                for keyword in keyword_list:
                    if keyword in content:
                        clearances[clearance_type] = True
                        logger.info(f"Keyword found: {keyword} for {clearance_type}")
                        break
            
            logger.info(f"Document content length: {len(content)} characters")
            logger.info(f"Detected clearances: {clearances}")
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
        
        return clearances
