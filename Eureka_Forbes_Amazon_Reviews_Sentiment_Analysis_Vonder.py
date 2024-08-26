import os
import re
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

# Ensure NLTK data path includes the custom path
nltk_data_path = '/Users/adwivedi/nltk_data'
nltk.data.path.append(nltk_data_path)

# Verify the required NLTK resources exist
required_paths = {
    'vader_lexicon': 'sentiment/vader_lexicon/vader_lexicon.txt',
    'punkt': 'tokenizers/punkt/english.pickle',
    'stopwords': 'corpora/stopwords/english',
    'wordnet': 'corpora/wordnet'
}

for resource, path in required_paths.items():
    full_path = os.path.join(nltk_data_path, path)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Expected {resource} file not found at: {full_path}")

# Initialize the SentimentIntensityAnalyzer with the local vader_lexicon.txt
sia = SentimentIntensityAnalyzer(lexicon_file=os.path.join(nltk_data_path, required_paths['vader_lexicon']))

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

# Categorize the sentiment into three categories
def categorize_sentiment(score):
    if score > 0.05:
        return "Positive"
    elif score < -0.05:
        return "Negative"
    else:
        return "Neutral"

def get_soup(url):
    splash_url = 'http://localhost:8050/render.html'
    params = {'url': url, 'wait': 2}
    r = requests.get(splash_url, params=params)
    return BeautifulSoup(r.text, 'html.parser')

def get_reviews(soup, asin):
    reviews = soup.find_all('div', {'data-hook': 'review'})
    review_batch = []
    for item in reviews:
        try:
            review_date = item.find('span', {'data-hook': 'review-date'}).text.strip()
            review_date = review_date.replace("Reviewed in India on ", "").strip()
            review_date = datetime.strptime(review_date, '%d %B %Y').strftime('%d-%m-%Y')
            year = datetime.strptime(review_date, '%d-%m-%Y').year
            product_name = soup.find('a', {'data-hook': 'product-link'}).text.split('|')[0].strip()
            body = item.find('span', {'data-hook': 'review-body'}).text.strip()
            cleaned_body = clean_text(body)
            review = {
                'asin': asin,
                'product_name': product_name,
                'year': year,
                'date': review_date,
                'rating': float(item.find('i', {'data-hook': 'review-star-rating'}).text.replace('out of 5 stars', '').strip()),
                'body': body,
                'cleaned_body': cleaned_body
            }
            review_batch.append(review)
        except Exception as e:
            print(f"An error occurred: {e}")
    return review_batch

reviewlist = []
asins = ['B0CW5YZ6VV', 'B096NTB9XT', 'B0CJTXNYVN', 'B09VS25ZX7', 'B0CJJ2CPXX' ]

for asin in asins:
    for x in range(2):  # Fetch up to 50 pages of reviews for each ASIN
        soup = get_soup(f'https://www.amazon.co.in/product-reviews/{asin}/ref=cm_cr_arp_d_viewopt_srt?ie=UTF8&reviewerType=all_reviews&pageNumber={x+1}&sortBy=recent')
        print(f'Getting page: {x + 1} for ASIN: {asin}')
        review_batch = get_reviews(soup, asin)
        reviewlist.extend(review_batch)
        print(f'Total reviews collected so far: {len(reviewlist)}')

# Convert the list of reviews into a DataFrame
df = pd.DataFrame(reviewlist, columns=['asin', 'product_name', 'year', 'date', 'rating', 'body', 'cleaned_body'])

# Display the first 5 and last 5 reviews before sentiment analysis
print("First 5 Reviews Before Sentiment Analysis:")
print(df.head(5).to_string(index=False))
print("\nLast 5 Reviews Before Sentiment Analysis:")
print(df.tail(5).to_string(index=False))

# Perform sentiment analysis and categorize sentiment
df['sentiment_score'] = df['cleaned_body'].apply(lambda x: sia.polarity_scores(x)['compound'])
df['sentiment_category'] = df['sentiment_score'].apply(categorize_sentiment)

# Display the first 5 and last 5 reviews after sentiment analysis
print("\nFirst 5 Reviews After Sentiment Analysis:")
print(df.head(5)[['asin', 'product_name', 'year', 'date', 'rating', 'cleaned_body', 'sentiment_score', 'sentiment_category']].to_string(index=False))
print("\nLast 5 Reviews After Sentiment Analysis:")
print(df.tail(5)[['asin', 'product_name', 'year', 'date', 'rating', 'cleaned_body', 'sentiment_score', 'sentiment_category']].to_string(index=False))

# Get the current date and time
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Save the final CSV with sentiment analysis
final_file_path = os.path.join(os.getcwd(), f'amazon_product_reviews_with_sentiment_{timestamp}.csv')
df.to_csv(final_file_path, index=False)
print(f'Reviews with sentiment saved to {final_file_path}')
