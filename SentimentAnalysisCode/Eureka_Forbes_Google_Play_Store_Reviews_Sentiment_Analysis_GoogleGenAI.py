import os
import re
import json
import time
from datetime import datetime
from google_play_scraper import Sort, reviews
import pandas as pd
import google.generativeai as genai


# Configure the Google Gemini API
GOOGLE_API_KEY = 'kAJSFGKFGAJKHSGFASGFGASGF'  # Replace with your actual API key
genai.configure(api_key=GOOGLE_API_KEY)

# List available models and select the Gemini model
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)

model = genai.GenerativeModel('gemini-1.0-pro')  # Replace with the correct model name if different

# Fetch reviews from Google Play Store
app_id = 'com.efl.eurekaforbes'
result, continuation_token = reviews(
    app_id,
    lang='en',  # language
    country='in',  # country
    sort=Sort.NEWEST,  # Sort order, 'newest' first
    count=10,  # Number of reviews
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

# Clean the review text
def clean_text(text):
    # Replace newline characters and strip leading/trailing whitespace
    text = text.replace("\n", " ").strip()

    # Remove non-ASCII characters and emojis
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)

    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)

    return text


mydata['cleaned_review'] = mydata['review'].apply(clean_text)
mydata['sentiment_category'] = ''  # Placeholder for sentiment

# Batch processing for Gemini API
batch_size = 25
batches = [mydata[i:i + batch_size] for i in range(0, mydata.shape[0], batch_size)]

def gemini_completion_function(batch, current_batch, total_batch):
    print(f"Now processing batch#: {current_batch+1} of {total_batch}")

    json_data = batch[['cleaned_review', 'sentiment_category']].to_json(orient='records')

    prompt = f"""
    You are an expert in linguistic analysis specializing in sentiment classification. Your task is to classify the sentiment of customer reviews into two categories: Positive (label=1) and Negative (label=0).

    Below is a JSON object containing customer reviews under the key 'cleaned_review'. Your job is to update the 'sentiment_category' field within the JSON with either 1 (Positive) or 0 (Negative) based on the sentiment expressed in the review.

    Please follow these rules:
    1. Only return the updated JSON object as output.
    2. Do not alter the structure or format of the JSON object.
    3. If a review violates API policy or contains any content issues, assign it a sentiment of 0 (Negative).

    Reviews are provided between three backticks below:

    {json_data}
    """

    try:
        response = model.generate_content(prompt)
        time.sleep(5)

        # Check if the response contains valid content
        if response.candidates and 'text' in response.candidates[0]:
            return response.candidates[0]['text'].strip("`")
        else:
            print("Response blocked or invalid; assigning Negative sentiment.")
            return json_data.replace('"sentiment_category": ""', '"sentiment_category": 0')

    except Exception as e:
        print(f"Error during API call: {e}")
        return json_data.replace('"sentiment_category": ""', '"sentiment_category": 0')


responses = [gemini_completion_function(batches[i], i, len(batches)) for i in range(len(batches))]

# Process responses and update DataFrame
df_total = pd.DataFrame()

for response in responses:
    try:
        data = json.loads(response)
        df_temp = pd.DataFrame(data)
        df_total = pd.concat([df_total, df_temp], ignore_index=True)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")

# Ensure the lengths match by slicing the DataFrame if necessary
if len(df_total) != len(mydata):
    print(f"Warning: Length mismatch. Trimming to minimum length of {min(len(df_total), len(mydata))}")
    mydata = mydata.iloc[:min(len(df_total), len(mydata))]
    df_total = df_total.iloc[:min(len(df_total), len(mydata))]

# Merge the updated sentiment data back into the original DataFrame
mydata['sentiment'] = df_total['sentiment_category'].values

# Map the sentiment values to the sentiment_category
sentiment_mapping = {0: "Negative", 1: "Positive"}
mydata['sentiment_category'] = mydata['sentiment'].map(sentiment_mapping)

# Get the current date and time
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Save the reviews with sentiment analysis to a separate CSV file
sentiment_reviews_file_path = os.path.join(os.getcwd(), f'google_playstore_reviews_with_gemini_sentiment_{timestamp}.csv')
mydata.to_csv(sentiment_reviews_file_path, index=False)
print(f'Reviews with sentiment analysis saved to {sentiment_reviews_file_path}')

# Display the first 5 and last 5 reviews after sentiment analysis
print("First 5 Reviews After Sentiment Analysis:")
print(mydata.head(5).to_string(index=False))

print("Last 5 Reviews After Sentiment Analysis:")
print(mydata.tail(5).to_string(index=False))
