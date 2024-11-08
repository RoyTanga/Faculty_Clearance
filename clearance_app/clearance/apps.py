from django.apps import AppConfig
from django.conf import settings
import os

class ClearanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clearance'

    def ready(self):
        from .clearance_classifier import ClearanceClassifier
        
        # Define the paths
        model_dir = os.path.join(settings.BASE_DIR, 'clearance', 'models')
        csv_path = os.path.join(settings.BASE_DIR, 'clearance_dataset.csv')
        
        # Initialize and train the classifier
        classifier = ClearanceClassifier(model_dir, csv_path)
        classifier.train(csv_path)
