from pathlib import Path
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import datetime
import serpapi
from typing import Optional
import re

# Load environment variables from .env file if it exists
load_dotenv()


def filter_reviews_by_date(data, start_date, end_date):
    """
    Filter reviews by date range and return a DataFrame with Date and Review columns.
    
    Parameters:
    -----------
    data : list of dict
        List of review dictionaries containing 'iso_date' and 'snippet' fields
    start_date : str or datetime
        Start date in format 'YYYY-MM-DD' or datetime object
    end_date : str or datetime
        End date in format 'YYYY-MM-DD' or datetime object
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with 'Date' and 'Review' columns filtered by date range
    """
    # Convert string dates to datetime objects if needed
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Extract date and review from data
    filtered_data = []
    
    for review in data:
        # Parse the iso_date string to datetime
        #review_date = datetime.fromisoformat(review['iso_date'].replace('Z', '+00:00'))
        review_date = pd.to_datetime(review['date'], errors='coerce')
        #print (review_date)
        
        # Check if the review date falls within the range (comparing dates only)
        review_date_only = review_date.date()
        start_date_only = start_date.date() if hasattr(start_date, 'date') else start_date
        end_date_only = end_date.date() if hasattr(end_date, 'date') else end_date
        
        if start_date_only <= review_date_only <= end_date_only:
            filtered_data.append({
                'Date': review_date_only,
                'Review': review['snippet']
            })
    
    # Create DataFrame
    df = pd.DataFrame(filtered_data)

    # Sort by Date in descending order (latest first)
    if not df.empty:
        df = df.sort_values(by='Date', ascending=False).reset_index(drop=True)
    
    return df


def fetch_reviews(client, product_id, START_DATE, END_DATE):
    df = pd.DataFrame(columns=["Date", "Review"])

    results = client.search(
    engine = "google_play_product",
    product_id = product_id,
    store = "apps",
    all_reviews = "true",
    num = 199,
    sort_by = 2,
    json_restrictor = "reviews, serpapi_pagination",
    )
    

    while "serpapi_pagination" in results:

        temp_df = filter_reviews_by_date(results["reviews"], START_DATE, END_DATE)
        if len(temp_df)==0:
            break
        df = pd.concat ([df, temp_df], ignore_index=True)
        
        results = client.search(
            engine = "google_play_product",
            product_id = product_id,
            store = "apps",
            all_reviews = True,
            num = 199,
            sort_by = 2,
            json_restrictor = "reviews, serpapi_pagination",
            next_page_token = results["serpapi_pagination"]["next_page_token"],    
        )

        

        # Sort by Date in descending order
        if not df.empty:
            df = df.sort_values(by='Date', ascending=False).reset_index(drop=True)   

    return df

def extract_play_store_id(url: str) -> Optional[str]:
    """
    Extract the product ID from various Google Play Store URL formats.
    
    Args:
        url: A Google Play Store URL (browser, mobile, or short link)
        
    Returns:
        The package ID (e.g., 'com.example.app') or None if not found
    """
    if not url or not isinstance(url, str):
        return None
    
    # Remove whitespace
    url = url.strip()
    
    # Pattern 1: Standard web URL
    # https://play.google.com/store/apps/details?id=com.example.app
    web_pattern = r'[?&]id=([a-zA-Z0-9._]+)'
    
    # Pattern 2: Short URL
    # https://play.app.goo.gl/?link=https://play.google.com/store/apps/details?id=com.example.app
    short_pattern = r'link=https?://play\.google\.com/store/apps/details\?id=([a-zA-Z0-9._]+)'
    
    # Pattern 3: Market URL (used by mobile apps)
    # market://details?id=com.example.app
    market_pattern = r'market://details\?id=([a-zA-Z0-9._]+)'
    
    # Pattern 4: Direct package ID path style
    # https://play.google.com/store/apps/details/com.example.app
    path_pattern = r'/details/([a-zA-Z0-9._]+)'
    
    # Try each pattern
    match = re.search(short_pattern, url)
    if match:
        return match.group(1)
    
    match = re.search(web_pattern, url)
    if match:
        return match.group(1)
    
    match = re.search(market_pattern, url)
    if match:
        return match.group(1)
    
    match = re.search(path_pattern, url)
    if match and '?id=' not in url:
        return match.group(1)
    
    # If no pattern matched, return None
    return None


