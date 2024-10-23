# -*- coding: utf-8 -*-
"""
train.ipynb

Full Code Implementation for multi-label classification model.
"""

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

class ClearanceClassifier:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        # Wrap MultinomialNB with OneVsRestClassifier for multi-label classification
        self.classifier = OneVsRestClassifier(MultinomialNB())
        self.mlb = MultiLabelBinarizer()
        self.is_fitted = False

    def preprocess_data(self, data):
        """
        Preprocess the data by converting boolean columns into string labels
        and creating a text representation of the clearances.
        """
        bool_columns = ['Admin_Clearance', 'Research_Clearance', 'Grade_Submission', 'Library_Clearance', 'Equipment_Returned']
        
        # Create a new 'Clearances' column that stores the names of columns where the value is 1 (i.e., clearance granted)
        data['Clearances'] = data[bool_columns].apply(lambda x: [col for col in bool_columns if x[col] == 1], axis=1)
        
        # Create a 'ClearanceText' column that concatenates the column names where clearance was granted
        data['ClearanceText'] = data['Clearances'].apply(lambda x: ' '.join(x))
        
        return data

    def train(self, csv_path):
        """
        Train the classifier with data from the provided CSV file.
        """
        try:
            # Load and preprocess the data
            data = pd.read_csv(csv_path)
            data = self.preprocess_data(data)

            # Prepare features and labels
            X = self.vectorizer.fit_transform(data['ClearanceText'])
            y = self.mlb.fit_transform(data['Clearances'])

            # Split the data into training and testing sets
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
        """
        Classify the faculty based on the provided clearances.
        """
        if not self.is_fitted:
            print("Error: The model has not been trained yet.")
            return None

        try:
            # Convert the input clearances to a string format
            clearance_text = ' '.join([col for col, val in clearances.items() if val])

            # Transform the text into the correct format for prediction
            X = self.vectorizer.transform([clearance_text])
            
            # Predict with the trained classifier
            y_pred = self.classifier.predict(X)
            
            # Transform back to the original clearance labels
            predicted_clearances = self.mlb.inverse_transform(y_pred)[0]
            
            return predicted_clearances
        except Exception as e:
            print(f"An error occurred during classification: {str(e)}")
            return None

    def save_model(self, output_dir):
        """
        Save the trained model components to the specified output directory.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Saving models
        joblib.dump(self.vectorizer, os.path.join(output_dir, 'vectorizer.pkl'))
        joblib.dump(self.classifier, os.path.join(output_dir, 'classifier.pkl'))
        joblib.dump(self.mlb, os.path.join(output_dir, 'mlb.pkl'))
        
        print(f"Models saved in {output_dir}")

    def load_model(self, model_dir):
        """
        Load the trained model components from the specified directory.
        """
        try:
            self.vectorizer = joblib.load(os.path.join(model_dir, 'vectorizer.pkl'))
            self.classifier = joblib.load(os.path.join(model_dir, 'classifier.pkl'))
            self.mlb = joblib.load(os.path.join(model_dir, 'mlb.pkl'))
            self.is_fitted = True
            print("Model loaded successfully")
        except FileNotFoundError:
            print("Error: Model files not found. Please check the model directory.")
        except Exception as e:
            print(f"An error occurred while loading the model: {str(e)}")


# Main function to simulate the process
def main():
    # Instantiate the classifier
    classifier = ClearanceClassifier()

    # Example file path for CSV file
    csv_file_path = '/Users/roytanga/Desktop/Work APT3065A/Clearance Prof/clearance_dataset.csv'

    # Train the model using the CSV file
    classifier.train(csv_file_path)

    # Save the trained model to a directory
    model_dir = 'models'
    classifier.save_model(model_dir)

    # Load the trained model
    classifier.load_model(model_dir)

    # Example of classifying a new set of clearances
    new_clearances = {
        'Admin_Clearance': 1,
        'Research_Clearance': 0,
        'Grade_Submission': 1,
        'Library_Clearance': 1,
        'Equipment_Returned': 0
    }
    predicted_clearances = classifier.classify_faculty(new_clearances)
    if predicted_clearances is not None:
        print(f"Predicted clearances: {predicted_clearances}")


# Run the main function if the script is executed
if __name__ == "__main__":
    main()
