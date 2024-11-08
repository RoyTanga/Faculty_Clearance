# -*- coding: utf-8 -*-
"""train.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1bzFpJ6AE58oz0GiPMfupXa8pr_Bz8wTX
"""

from importlib.metadata import files
import pandas as pd
import io
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.multiclass import OneVsRestClassifier
import joblib
import os

# Load and preprocess the data
def load_and_preprocess_data(file_content):
    # Load the data using io.StringIO to handle the file content
    data = pd.read_csv(io.StringIO(file_content))

    # Define boolean columns
    bool_columns = ['Admin_Clearance', 'Research_Clearance', 'Grade_Submission', 'Library_Clearance', 'Equipment_Returned']

    # Convert boolean columns to descriptive strings
    for col in bool_columns:
        data[col] = data[col].map({1: col, 0: f'No_{col}'})

    # Combine all clearance columns into a single list for each row
    data['Clearances'] = data[bool_columns].apply(lambda x: [col for col in x if col != f'No_{col}'], axis=1)

    # Create a text representation of all clearances
    data['ClearanceText'] = data[bool_columns].apply(lambda x: ' '.join([col for col in x if col != f'No_{col}']), axis=1)

    return data

# Train the model
def train_model(data):
    # Initialize TfidfVectorizer and MultiLabelBinarizer
    vectorizer = TfidfVectorizer()
    mlb = MultiLabelBinarizer()

    # Prepare features and labels
    X = vectorizer.fit_transform(data['ClearanceText'])
    y = mlb.fit_transform(data['Clearances'])

    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Use OneVsRestClassifier to handle multi-label classification
    classifier = OneVsRestClassifier(MultinomialNB())
    classifier.fit(X_train, y_train)

    # Make predictions
    y_pred = classifier.predict(X_test)

    # Evaluate the model
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=mlb.classes_)

    print(f"Model Accuracy: {accuracy}")
    print("\nClassification Report:\n", report)

    return vectorizer, classifier, mlb

# Save the model components
def save_model(vectorizer, classifier, mlb, output_dir):
    # Create the directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Save the models
    joblib.dump(vectorizer, os.path.join(output_dir, 'vectorizer.joblib'))
    joblib.dump(classifier, os.path.join(output_dir, 'classifier.joblib'))
    joblib.dump(mlb, os.path.join(output_dir, 'mlb.joblib'))

    print(f"Models saved in {output_dir}")

# Main function
def main():
    # Simulate file upload

    uploaded = files.upload()

    # Assuming only one file is uploaded
    file_name = list(uploaded.keys())[0]
    file_content = uploaded[file_name].decode('utf-8')

    output_dir = 'models'  # Directory to save the model components

    try:
        # Load and preprocess the data
        data = load_and_preprocess_data(file_content)

        # Train the model
        vectorizer, classifier, mlb = train_model(data)

        # Save the model
        save_model(vectorizer, classifier, mlb, output_dir)

    except pd.errors.EmptyDataError:
        print(f"Error: The file '{file_name}' is empty. Please check the file contents and try again.")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

# Run the main function
if __name__ == "__main__":
    main()

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import MultiLabelBinarizer
import os

class ClearanceClassifier:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        self.classifier = MultinomialNB()
        self.mlb = MultiLabelBinarizer()
        self.is_fitted = False

    def preprocess_data(self, data):
        bool_columns = ['Admin_Clearance', 'Research_Clearance', 'Grade_Submission', 'Library_Clearance', 'Equipment_Returned']
        for col in bool_columns:
            data[col] = data[col].map({1: col, 0: f'No_{col}'})
        data['Clearances'] = data[bool_columns].apply(lambda x: [col for col in x.index if x[col] == col], axis=1)
        data['ClearanceText'] = data[bool_columns].apply(lambda x: ' '.join([col for col in x.index if x[col] == col]), axis=1)
        return data

    def train(self, csv_path):
        try:
            # Load and preprocess the data
            data = pd.read_csv(csv_path)
            data = self.preprocess_data(data)

            # Prepare features and labels
            X = self.vectorizer.fit_transform(data['ClearanceText'])
            y = self.mlb.fit_transform(data['Clearances'])

            # Split the data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            # Train the classifier
            self.classifier.fit(X_train, y_train)

            # Set the fitted flag
            self.is_fitted = True

            # Evaluate the model
            y_pred = self.classifier.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            report = classification_report(y_test, y_pred, target_names=self.mlb.classes_)

            print(f"Model accuracy: {accuracy}")
            print("\nClassification Report:")
            print(report)

        except FileNotFoundError:
            print(f"Error: The file '{csv_path}' was not found.")
        except pd.errors.EmptyDataError:
            print(f"Error: The file '{csv_path}' is empty.")
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")

    def classify_faculty(self, clearances):
        if not self.is_fitted:
            print("Error: The model has not been trained yet.")
            return None

        try:
            clearance_text = ' '.join([col for col, val in clearances.items() if val])
            X = self.vectorizer.transform([clearance_text])
            y_pred = self.classifier.predict(X)
            predicted_clearances = self.mlb.inverse_transform(y_pred)[0]
            return predicted_clearances
        except Exception as e:
            print(f"An error occurred during classification: {str(e)}")
            return None

