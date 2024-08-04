import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import datetime, timedelta
import concurrent.futures
import csv
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

# Download necessary NLTK resources
nltk.download('punkt')

# Function to categorize the news based on keywords
def categorize_news(headline, content):
    categories = {
        "Politics": ["election", "government", "policy", "politician"],
        "International News": ["world", "international", "foreign"],
        "National News": ["india", "national"],
        "Local News": ["local", "city", "town"],
        "Business and Finance": ["business", "finance", "market", "economy"],
        "Science and Technology": ["science", "technology", "tech", "research"],
        "Health and Wellness": ["health", "wellness", "medical", "fitness"],
        "Entertainment": ["entertainment", "movie", "film", "music"],
        "Sports": ["sport", "game", "tournament", "match"],
        "Lifestyle and Features": ["lifestyle", "feature", "trend"],
        "Opinion and Editorial": ["opinion", "editorial"],
        "Environment": ["environment", "climate", "nature"],
        "Education": ["education", "school", "college", "university"],
        "Crime and Justice": ["crime", "justice", "law", "court"],
        "Human Interest": ["human interest", "story", "people"],
        "Obituaries": ["obituary", "death", "passed away"],
        "Weather": ["weather", "forecast", "rain", "temperature"],
        "Religion and Spirituality": ["religion", "spirituality", "faith"],
        "Technology and Gadgets": ["technology", "gadget", "device"],
        "Automotive": ["car", "automobile", "vehicle"]
    }
    
    text = (headline + " " + content).lower()
    
    for category, keywords in categories.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "General News"

# Function to fetch and parse the news articles for a specific date
def fetch_news(year, month, day, starttime, collected_urls, max_articles):
    archive_url = f'https://timesofindia.indiatimes.com/{year}/{month}/{day}/archivelist/year-{year},month-{month},starttime-{starttime}.cms'
    print(f"Fetching news for {day}/{month}/{year} from URL: {archive_url}")
    try:
        response = requests.get(archive_url)
        response.raise_for_status()  # Raise an exception for HTTP errors
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {archive_url}: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    span_tags = soup.find_all('span', style="font-family:arial ;font-size:12;color: #006699")
    if not span_tags:
        print(f"No articles found for {day}/{month}/{year}.")
    news_list = []
    for span in span_tags:
        articles = span.find_all('a', href=True)
        for article in articles:
            article_url = article['href']
            if 'articleshow' not in article_url:
                continue
            if article_url.startswith('/'):
                article_url = f"https://timesofindia.indiatimes.com{article_url}"
            if article_url not in collected_urls and len(news_list) + len(collected_urls) < max_articles:
                collected_urls.add(article_url)
                headline_text = article.get_text(strip=True)
                content_text = fetch_article_content(article_url)
                summary_text = summarize_text(content_text)  # Using the new summarization logic
                category = categorize_news(headline_text, content_text)
                news = {
                    "Newspaper": "The Times of India",
                    "Link": article_url,
                    "Headline": headline_text,
                    "Content": content_text,
                    "Summary": summary_text,
                    "Category": category,
                    "Date": f"{day:02}/{month:02}/{year}"
                }
                news_list.append(news)
    return news_list

# Function to fetch the content of a news article
# def fetch_article_content(url):
#     print(f"Fetching content from {url}")
#     try:
#         response = requests.get(url)
#         response.raise_for_status()  # Raise an exception for HTTP errors
#     except requests.exceptions.RequestException as e:
#         print(f"Error fetching URL {url}: {e}")
#         return "Content not available"
    
#     soup = BeautifulSoup(response.text, 'html.parser')
#     headline = soup.find('h1', class_='HNMDR')
#     content_div = soup.find('div', class_='_s30J clearfix')
    
#     if headline:
#         headline_text = headline.get_text(strip=True)
#     else:
#         headline_text = "Headline not available"
        
#     if content_div:
#         content_text = content_div.get_text(strip=True)
#     else:
#         content_text = "Content not available"
        
#     return f"{headline_text}\n{content_text}"
def fetch_article_content(url):
    print(f"Fetching content from {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return "Content not available"
    
    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.content, 'html.parser')
    headline = soup.find('h1', class_='HNMDR')
    content_div = soup.find('div', class_='_s30J clearfix')
    
    if headline:
        headline_text = headline.get_text(strip=True)
    else:
        headline_text = "Headline not available"
        
    if content_div:
        content_text = content_div.get_text(strip=True)
    else:
        content_text = "Content not available"
        
    return f"{headline_text}\n{content_text}"
# Function to summarize the text
def summarize_text(text, max_words=250):
    """
    Summarize the text to approximately max_words by extracting key sentences.
    """
    sentences = sent_tokenize(text)
    summarized = ""
    word_count = 0
    
    for sentence in sentences:
        words_in_sentence = word_tokenize(sentence)
        if word_count + len(words_in_sentence) > max_words:
            break
        summarized += sentence + " "
        word_count += len(words_in_sentence)
    
    return summarized.strip()

# Function to calculate the starttime parameter
def calculate_starttime(base_starttime, date):
    base_date = datetime(2010, 1, 1)
    target_date = datetime(date.year, date.month, date.day)
    delta = target_date - base_date
    return base_starttime + delta.days

# Main function to iterate through the date range and collect news
# def collect_news(start_year, start_month, start_day, end_year, end_month, end_day, max_news):
#     base_starttime = 40179
#     collected_urls = set()
#     news_list = []
#     current_date = datetime(start_year, start_month, start_day)
#     end_date = datetime(end_year, end_month, end_day)
#     total_news_count = 0

#     with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
#         future_to_date = {executor.submit(fetch_news, current_date.year, current_date.month, current_date.day, calculate_starttime(base_starttime, current_date), collected_urls, max_news): current_date for _ in range((end_date - current_date).days + 1)}
        
#         for future in concurrent.futures.as_completed(future_to_date):
#             news_day_list = future.result()
#             news_list.extend(news_day_list)
#             total_news_count += len(news_day_list)
            
#             # Print progress at regular intervals
#             if total_news_count % 100 == 0 and total_news_count > 0:
#                 print(f"Collected {total_news_count} news articles so far.")
#                 break  # Stop after collecting 100 news articles

#             # Update to the next day
#             current_date += timedelta(days=1)

#     return news_list
def collect_news(start_year, start_month, start_day, end_year, end_month, end_day, max_news):
    base_starttime = 40179
    collected_urls = set()
    news_list = []
    current_date = datetime(start_year, start_month, start_day)
    end_date = datetime(end_year, end_month, end_day)
    total_news_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_date = {}
        while current_date <= end_date and total_news_count < max_news:
            future = executor.submit(fetch_news, current_date.year, current_date.month, current_date.day, 
                                     calculate_starttime(base_starttime, current_date), collected_urls, 
                                     max_news - total_news_count)
            future_to_date[future] = current_date
            current_date += timedelta(days=1)

        for future in concurrent.futures.as_completed(future_to_date):
            news_day_list = future.result()
            news_list.extend(news_day_list)
            total_news_count += len(news_day_list)
            
            print(f"Collected {total_news_count} news articles so far.")
            
            if total_news_count >= max_news:
                break

    return news_list[:max_news]  # Ensure we return exactly max_news articles


# Save the collected news to a CSV file
def save_to_csv(news_list, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["Newspaper", "Link", "Headline", "Content", "Summary", "Category", "Date"], quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for news in news_list:
            writer.writerow(news)

# Parameters
start_year = 2011
start_month = 1
start_day = 1
end_year = 2011
end_month = 1
end_day = 15  # Collect news for the first 15 days of January 2010
max_news = 10 # Stop after collecting 100 news articles for testing
filename = 'dummy_news_archive.csv'

# Collect and save news
news_list = collect_news(start_year, start_month, start_day, end_year, end_month, end_day, max_news)
save_to_csv(news_list, filename)

print(f'Collected {len(news_list)} news articles and saved to {filename}')
