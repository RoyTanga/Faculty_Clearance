import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
import joblib

# Load your dataset (example: a CSV with 'document_text' and 'category' columns)
data = pd.read_csv('clearance_dataset.csv')

# Split data into training and test sets
X = data['document_text']
y = data['category']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Convert documents to TF-IDF features
vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)

# Train a classifier
classifier = RandomForestClassifier()
classifier.fit(X_train_tfidf, y_train)

# Save the model and vectorizer for later use in the Flask app
joblib.dump(classifier, 'document_classifier.pkl')
joblib.dump(vectorizer, 'tfidf_vectorizer.pkl')

# Evaluate the model (optional)
accuracy = classifier.score(X_test_tfidf, y_test)
print(f'Model accuracy: {accuracy * 100:.2f}%')
