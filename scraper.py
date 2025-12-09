import requests
import json
import time
import os
from datetime import datetime

# --- CONFIGURATION ---
OUTPUT_FILE = 'lore_data.json'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

TARGET_SUBREDDITS = [
    'EldenRingLoreTalk',
    'eldenringlore'
]
SEARCH_QUERIES = ['flair:"Lore Theory"', 'title:timeline', 'title:"deep dive"']

# Rate limit settings
SLOW_MODE = True  # Set to True to avoid rate limits (takes longer)
DELAY_BETWEEN_POSTS = 3 if SLOW_MODE else 1.5
DELAY_BETWEEN_PAGES = 5 if SLOW_MODE else 2
DELAY_BETWEEN_SORTS = 10 if SLOW_MODE else 5

LORE_TOPICS = {
    "Outer Gods": ["greater will", "frenzied flame", "formless mother", "fell god"],
    "Demigods": ["ranni", "miquella", "malenia", "radahn", "morgott", "mohg", "messmer"],
    "History": ["numen", "nox", "marika", "radagon", "erdtree", "crucible"],
    "Death": ["godskin", "black flame", "maliketh", "destined death", "gloam"],
    "Dragons": ["placidusax", "bayle", "farum azula", "drake"]
}

def fetch_json(url, params=None, retry_count=0):
    headers = {'User-Agent': USER_AGENT}
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            wait_time = 60 * (retry_count + 1)  # Exponential backoff
            print(f"  !! Rate limit (429). Waiting {wait_time}s...")
            time.sleep(wait_time)
            if retry_count < 3:
                return fetch_json(url, params, retry_count + 1)
            return None
        return None
    except Exception as e:
        print(f"  !! Error: {e}")
        return None

def get_comments(permalink):
    """
    Fetches the specific post JSON to get full comments.
    Limit: Top 3 comments to keep file size reasonable.
    """
    url = f"https://www.reddit.com{permalink}.json"
    data = fetch_json(url, {'sort': 'top', 'limit': 5})
    
    comments = []
    if data and len(data) > 1:
        # Reddit JSON structure: [0] is post, [1] is comments
        comment_tree = data[1].get('data', {}).get('children', [])
        
        for c in comment_tree:
            c_data = c.get('data', {})
            body = c_data.get('body', '')
            
            # Filter out bots and short garbage
            if body and c_data.get('score', 0) > 5 and len(body) > 30 and "I am a bot" not in body:
                comments.append({
                    "body": body,
                    "score": c_data.get('score', 0)
                })
                if len(comments) >= 3: break # Limit to top 3 insights
                
    return comments

def determine_category(text):
    text = text.lower()
    for category, keywords in LORE_TOPICS.items():
        if any(k in text for k in keywords):
            return category
    return "General Lore"

def scrape_and_save():
    all_posts = []
    seen_ids = set()

    print(f"--- Starting Deep Scrape (No-API Mode) ---")

    for sub in TARGET_SUBREDDITS:
        print(f"Scanning r/{sub}...")
        
        # Scrape fewer sorting methods for faster scraping
        sort_methods = [
            ('hot', None, 50),
            ('new', None, 50),
            ('best', None, 50)
        ]
        
        for sort_idx, (sort_type, time_filter, limit) in enumerate(sort_methods):
            if sort_idx > 0:
                print(f"  Cooling down {DELAY_BETWEEN_SORTS}s before next sort method...")
                time.sleep(DELAY_BETWEEN_SORTS)
            print(f"  Fetching {sort_type} posts...")
            url = f"https://www.reddit.com/r/{sub}/{sort_type}.json"
            params = {'limit': limit}
            if time_filter:
                params['t'] = time_filter
            
            after = None
            pages_fetched = 0
            max_pages = 2  # Fetch 2 pages per sort method for faster scraping
            
            while pages_fetched < max_pages:
                print(f"    Fetching page {pages_fetched + 1}/{max_pages}...")
                if after:
                    params['after'] = after
                    
                data = fetch_json(url, params)
                
                if not data:
                    break
                    
                posts = data.get('data', {}).get('children', [])
                after = data.get('data', {}).get('after')
                
                if not posts:
                    break
                
                for i, post in enumerate(posts):
                    p_data = post['data']
                    if p_data['id'] in seen_ids or p_data.get('stickied'): continue
                    
                    print(f"    [{len(all_posts)+1}] {p_data['title'][:50]}...")
                    
                    # Fetch Comments (The slow part)
                    comments = get_comments(p_data['permalink'])
                    
                    # Sleep to avoid rate limits
                    time.sleep(DELAY_BETWEEN_POSTS) 

                    # Extract image URL if available
                    image_url = None
                    if p_data.get('post_hint') == 'image':
                        image_url = p_data.get('url')
                    elif 'preview' in p_data and 'images' in p_data['preview']:
                        # Get the highest resolution preview image
                        try:
                            image_url = p_data['preview']['images'][0]['source']['url'].replace('&amp;', '&')
                        except (KeyError, IndexError):
                            pass

                    post_entry = {
                        "title": p_data['title'],
                        "url": p_data['url'],
                        "score": p_data['score'],
                        "subreddit": sub,
                        "body": p_data.get('selftext', ''),
                        "category": determine_category(p_data['title'] + " " + p_data.get('selftext', '')),
                        "scraped_at": datetime.now().isoformat(),
                        "image_url": image_url,
                        "comments": comments
                    }
                    all_posts.append(post_entry)
                    seen_ids.add(p_data['id'])
                
                pages_fetched += 1
                
                if not after:
                    break
                    
                print(f"    Pausing {DELAY_BETWEEN_PAGES}s before next page...")
                time.sleep(DELAY_BETWEEN_PAGES)

    # --- CRITICAL SAFETY CHECK ---
    if len(all_posts) == 0:
        print("!! ERROR: No posts found. Reddit blocked the request or API is down.")
        print("!! ABORTING: Existing data protected.")
        return 

    # Save to JSON
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        json.dump(all_posts, f, indent=2)
    
    print(f"Done! Saved {len(all_posts)} scrolls with insights to '{OUTPUT_FILE}'.")

if __name__ == "__main__":
    scrape_and_save()