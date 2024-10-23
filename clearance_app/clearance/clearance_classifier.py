import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.multiclass import OneVsRestClassifier
import joblib
import os
import logging

logging.basicConfig(level=logging.INFO)

class ClearanceClassifier:
    def __init__(self, model_dir, csv_path):
        self.vectorizer = None
        self.classifier = None
        self.mlb = None
        self.is_fitted = False
        self.model_dir = model_dir
        self.csv_path = csv_path

        logging.info(f"Initializing ClearanceClassifier with model_dir: {model_dir} and csv_path: {csv_path}")

        if os.path.exists(model_dir) and all(os.path.exists(os.path.join(model_dir, f)) for f in ['vectorizer.pkl', 'classifier.pkl', 'mlb.pkl']):
            logging.info("Found existing model files. Loading model...")
            self.load_model(model_dir)
        else:
            logging.info("No existing model found. Training new model...")
            self.train(csv_path)
            self.save_model(model_dir)

        logging.info(f"Initialization complete. Is fitted: {self.is_fitted}")

    def preprocess_data(self, data):
        bool_columns = ['Admin_Clearance', 'Research_Clearance', 'Grade_Submission', 'Library_Clearance', 'Equipment_Returned']
        data['Clearances'] = data[bool_columns].apply(lambda x: [col for col in bool_columns if x[col] == 1], axis=1)
        data['ClearanceText'] = data['Clearances'].apply(lambda x: ' '.join(x))
        return data

    def train(self, csv_path):
        try:
            logging.info(f"Starting training with CSV file: {csv_path}")
            data = pd.read_csv(csv_path)
            data = self.preprocess_data(data)

            self.vectorizer = TfidfVectorizer()
            self.classifier = OneVsRestClassifier(MultinomialNB())
            self.mlb = MultiLabelBinarizer()

            X = self.vectorizer.fit_transform(data['ClearanceText'])
            y = self.mlb.fit_transform(data['Clearances'])

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            self.classifier.fit(X_train, y_train)
            self.is_fitted = True  # Set is_fitted to True after successful training

            y_pred = self.classifier.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            report = classification_report(y_test, y_pred, target_names=self.mlb.classes_)

            logging.info(f"Model accuracy: {accuracy}")
            logging.info(f"Classification Report:\n{report}")

        except Exception as e:
            logging.error(f"An error occurred during training: {str(e)}")
            self.is_fitted = False  # Ensure is_fitted is False if training fails

    def classify_faculty(self, clearances):
        if not self.is_fitted:
            logging.error("Error: The model has not been trained yet.")
            return None

        try:
            clearance_text = ' '.join([col for col, val in clearances.items() if val])
            X = self.vectorizer.transform([clearance_text])
            y_pred = self.classifier.predict(X)
            predicted_clearances = self.mlb.inverse_transform(y_pred)[0]
            return list(predicted_clearances)
        except Exception as e:
            logging.error(f"An error occurred during classification: {str(e)}")
            return None

    def save_model(self, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        joblib.dump(self.vectorizer, os.path.join(output_dir, 'vectorizer.pkl'))
        joblib.dump(self.classifier, os.path.join(output_dir, 'classifier.pkl'))
        joblib.dump(self.mlb, os.path.join(output_dir, 'mlb.pkl'))
        logging.info(f"Models saved in {output_dir}")

    def load_model(self, model_dir):
        try:
            self.vectorizer = joblib.load(os.path.join(model_dir, 'vectorizer.pkl'))
            self.classifier = joblib.load(os.path.join(model_dir, 'classifier.pkl'))
            self.mlb = joblib.load(os.path.join(model_dir, 'mlb.pkl'))
            self.is_fitted = True
            logging.info("Model loaded successfully")
        except Exception as e:
            logging.error(f"An error occurred while loading the model: {str(e)}")
            self.is_fitted = False

    def is_model_fitted(self):
        return (hasattr(self.vectorizer, 'vocabulary_') and
                hasattr(self.classifier, 'classes_') and
                hasattr(self.mlb, 'classes_'))
