import os
import re
from datetime import datetime
from google_play_scraper import Sort, reviews
import pandas as pd
from transformers import pipeline


# Function to clean the review text
def clean_text(text):
    # Replace newline characters and strip leading/trailing whitespace
    text = text.replace("\n", " ").strip()

    # Remove non-ASCII characters and emojis
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)

    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)

    return text


# Initialize the transformers pipeline for sentiment analysis
sentiment_pipeline = pipeline("sentiment-analysis")

# Fetch reviews from Google Play Store
app_id = 'com.efl.eurekaforbes'
result, continuation_token = reviews(
    app_id,
    lang='en',
    country='in',
    sort=Sort.NEWEST,
    count=5000,
)

# Convert reviews to DataFrame
df = pd.DataFrame(result)

# Select necessary columns and rename them
mydata = df[['at', 'score', 'content']]
mydata.columns = ['date', 'app_rating', 'review']

# Add a new column 'year' by extracting it from the 'date' column
mydata['year'] = pd.to_datetime(mydata['date']).dt.year

# Reorder columns to place 'year' as the first column
mydata = mydata[['year', 'date', 'app_rating', 'review']]

# Format the date from "DD/MM/YY HH:MM" to "DD/MM/YY"
mydata['date'] = pd.to_datetime(mydata['date']).dt.strftime('%d/%m/%y')

# Display the first 5 and last 5 reviews before sentiment analysis
print("First 5 Reviews Before Sentiment Analysis:")
print(mydata.head(5).to_string(index=False))

print("Last 5 Reviews Before Sentiment Analysis:")
print(mydata.tail(5).to_string(index=False))

# Clean the review text
mydata['cleaned_review'] = mydata['review'].apply(clean_text)

# Apply sentiment analysis using the transformers pipeline
def analyze_sentiment(text):
    result = sentiment_pipeline(text)[0]
    score = result['score']
    label = result['label']
    if label == 'POSITIVE':
        return score, 'Positive'
    elif label == 'NEGATIVE':
        return score, 'Negative'
    else:
        return score, 'Neutral'

mydata[['sentiment', 'sentiment_category']] = mydata['cleaned_review'].apply(lambda x: pd.Series(analyze_sentiment(x)))

# Get the current date and time
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Save the reviews with sentiment analysis to a separate CSV file
sentiment_reviews_file_path = os.path.join(os.getcwd(), f'google_playstore_reviews_with_sentiment_transformers_{timestamp}.csv')

mydata.to_csv(sentiment_reviews_file_path, index=False)
print(f'Reviews with sentiment analysis saved to {sentiment_reviews_file_path}')

# Display the first 5 and last 5 reviews after sentiment analysis
print("First 5 Reviews After Sentiment Analysis:")
print(mydata.head(5).to_string(index=False))

print("Last 5 Reviews After Sentiment Analysis:")
print(mydata.tail(5).to_string(index=False))
