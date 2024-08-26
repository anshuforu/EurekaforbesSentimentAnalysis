import os
import pandas as pd
import re
from google_play_scraper import Sort, reviews
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from datetime import datetime

# Ensure NLTK data path includes the custom path
nltk_data_path = '/Users/adwivedi/nltk_data'
nltk.data.path.append(nltk_data_path)

# Verify the VADER lexicon file exists
vader_lexicon_path = os.path.join(nltk_data_path, 'sentiment/vader_lexicon', 'vader_lexicon.txt')
if not os.path.exists(vader_lexicon_path):
    raise FileNotFoundError(f"Expected VADER lexicon file not found at: {vader_lexicon_path}")

# Manually load the VADER lexicon
sia = SentimentIntensityAnalyzer(lexicon_file=vader_lexicon_path)

# Verify the punkt tokenizer exists
punkt_path = os.path.join(nltk_data_path, 'tokenizers/punkt/english.pickle')
if not os.path.exists(punkt_path):
    raise FileNotFoundError(f"Expected punkt tokenizer not found at: {punkt_path}")

# Verify the stopwords corpus exists
stopwords_path = os.path.join(nltk_data_path, 'corpora/stopwords/english')
if not os.path.exists(stopwords_path):
    raise FileNotFoundError(f"Expected stopwords corpus not found at: {stopwords_path}")

# Function to clean the review text
def clean_text(text):
    # Convert to lowercase
    text = text.lower()

    # Replace newline characters and strip leading/trailing whitespace
    text = text.replace("\n", " ").strip()

    # Remove non-ASCII characters and emojis
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)

    # Remove unwanted punctuation (keeping periods and commas)
    text = re.sub(r'[^\w\s.,]', '', text)

    # Remove numbers (optional, depending on if you want to keep numeric context)
    text = re.sub(r'\d+', '', text)

    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)

    # Replace multiple periods with a single period
    text = re.sub(r'\.+', '.', text)

    # Tokenize the text
    words = word_tokenize(text)

    # Use a less aggressive stopword removal (retain some stopwords for context)
    stop_words = set(stopwords.words('english')) - {'no', 'not', 'up', 'down', 'few', 'more'}

    # Remove stopwords, but retain some key ones for context
    words = [word for word in words if word not in stop_words]

    # Lemmatize the words
    lemmatizer = WordNetLemmatizer()
    words = [lemmatizer.lemmatize(word) for word in words]

    # Join words back to a single string
    cleaned_text = ' '.join(words)

    return cleaned_text

# Categorize the sentiment
def categorize_sentiment(score):
    if score > 0.05:
        return "Positive"
    elif score < -0.05:
        return "Negative"
    else:
        return "Neutral"

# Fetch reviews from Google Play Store
app_id = 'com.efl.eurekaforbes'
result, continuation_token = reviews(
    app_id,
    lang='en',  # language
    country='in',  # country
    sort=Sort.NEWEST,  # Sort order, 'newest' first
    count=5000,  # Number of reviews
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

# Apply sentiment analysis
mydata['sentiment'] = mydata['cleaned_review'].apply(lambda x: sia.polarity_scores(x)['compound'])

# Apply the categorization function
mydata['sentiment_category'] = mydata['sentiment'].apply(categorize_sentiment)

# Get the current date and time
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Save the reviews with sentiment analysis to a separate CSV file
sentiment_reviews_file_path = os.path.join(os.getcwd(), f'google_playstore_reviews_with_sentiment_vonder_{timestamp}.csv')

mydata.to_csv(sentiment_reviews_file_path, index=False)
print(f'Reviews with sentiment analysis saved to {sentiment_reviews_file_path}')

# Display the first 5 and last 5 reviews after sentiment analysis
print("First 5 Reviews After Sentiment Analysis:")
print(mydata.head(5).to_string(index=False))

print("Last 5 Reviews After Sentiment Analysis:")
print(mydata.tail(5).to_string(index=False))
