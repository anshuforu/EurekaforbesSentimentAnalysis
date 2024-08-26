import requests
from requests_html import HTML
import json

# Splash instance URL
splash_url = 'http://localhost:8050/render.html'

# Target URL to scrape
url = 'https://x.com/EurekaForbes/with_replies'

# Parameters for Splash request
params = {
    'url': url,
    'wait': 2,  # Wait time for JavaScript content to load
    'render_all': 1
}

# Make the request to Splash
response = requests.get(splash_url, params=params)

# Check if the request was successful
if response.status_code == 200:
    print("Successfully fetched the webpage")
else:
    print(f"Failed to fetch the webpage. Status code: {response.status_code}")

# Parse the HTML content
html = HTML(html=response.text)

# Extract tweets (adjust the CSS selector based on actual page structure)
tweets = html.find('.tweet')
if tweets:
    print(f"Found {len(tweets)} tweets")
    for tweet in tweets:
        print(tweet.text)
else:
    print("No tweets found")
