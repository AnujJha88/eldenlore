import requests
import json
import time
import os
from datetime import datetime

# --- CONFIGURATION ---
# No Client ID or Secret needed!
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
OUTPUT_FILE = 'lore_data.json'

TARGET_SUBREDDITS = ['eldenringlore', 'EldenRingLoreTalk']

# Queries to find deep lore
SEARCH_QUERIES = [
    'flair:"Lore Theory"', 
    'flair:"Speculation"', 
    'title:timeline',
    'title:"deep dive"'
]

LORE_TOPICS = {
    "The Outer Gods & Cosmos": ["greater will", "frenzied flame", "formless mother", "fell god", "dark moon", "astel", "fallingstar", "void", "stars"],
    "The Empyreans & Demigods": ["ranni", "miquella", "malenia", "radahn", "rykard", "morgott", "mohg", "godwyn", "messmer", "gloam-eyed", "trina"],
    "History & Factions": ["numen", "nox", "eternal city", "marika", "radagon", "golden order", "erdtree", "crucible", "misbegotten", "albinauric"],
    "Death & Destined Death": ["godskin", "black flame", "maliketh", "destined death", "deathroot", "fia", "those who live in death"],
    "Dragons & Beasts": ["placidusax", "gransax", "fortissax", "lansseax", "bayle", "farum azula", "beastman", "serosh"]
}

def fetch_json(url, params=None):
    """Helper to get data from Reddit without an API key"""
    headers = {'User-Agent': USER_AGENT}
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            print("  !! Rate limited. Sleeping for 5 seconds...")
            time.sleep(5)
            return fetch_json(url, params) # Retry
        else:
            print(f"  !! Error {response.status_code}: {url}")
            return None
    except Exception as e:
        print(f"  !! Connection Error: {e}")
        return None

def scrape_and_save():
    seen_ids = set()
    all_posts = []

    print(f"--- Starting No-API Scrape ---")

    for sub in TARGET_SUBREDDITS:
        print(f"Scanning r/{sub}...")
        
        # 1. Get Top Posts (Month)
        url = f"https://www.reddit.com/r/{sub}/top.json"
        data = fetch_json(url, {'t': 'month', 'limit': 75}) # Limit slightly lower to be safe
        
        if data:
            posts = data.get('data', {}).get('children', [])
            for post in posts:
                process_post_data(post['data'], all_posts, seen_ids)
        
        time.sleep(2) # Be polite to Reddit servers

        # 2. Search for specific queries
        search_url = f"https://www.reddit.com/r/{sub}/search.json"
        for query in SEARCH_QUERIES:
            print(f"  > Searching: {query}")
            params = {'q': query, 'restrict_sr': 'on', 'sort': 'top', 'limit': 30}
            data = fetch_json(search_url, params)
            
            if data:
                posts = data.get('data', {}).get('children', [])
                for post in posts:
                    process_post_data(post['data'], all_posts, seen_ids)
            
            time.sleep(2)

    # Save to JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_posts, f, indent=2)
    
    print(f"Done! Saved {len(all_posts)} discussions to '{OUTPUT_FILE}'.")

def process_post_data(post_raw, collection, seen_ids):
    pid = post_raw.get('id')
    if pid in seen_ids:
        return
    
    # Filter: Skip weak posts
    if post_raw.get('stickied') or post_raw.get('score', 0) < 10:
        return
    
    # Filter: Text length (Selftext)
    body = post_raw.get('selftext', '')
    if len(body) < 100:
        return

    seen_ids.add(pid)

    # Determine Category
    best_topic = "General Lore"
    text_content = (post_raw.get('title', '') + " " + body).lower()
    
    for topic, keywords in LORE_TOPICS.items():
        if any(k in text_content for k in keywords):
            best_topic = topic
            break

    # We can't easily fetch comments in "No-API" mode without making 
    # 100s of separate requests (which gets you banned). 
    # So we skip comments for now to keep it safe and fast.
    
    post_data = {
        "title": post_raw.get('title'),
        "url": post_raw.get('url'),
        "score": post_raw.get('score'),
        "subreddit": post_raw.get('subreddit'),
        "body": body,
        "category": best_topic,
        "scraped_at": datetime.now().isoformat(),
        "comments": [] # Leaving empty to avoid rate limits
    }
    
    collection.append(post_data)

if __name__ == "__main__":
    scrape_and_save()