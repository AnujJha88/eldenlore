import praw
import json
import os
from datetime import datetime
from collections import defaultdict

# --- CONFIGURATION ---
# These are loaded from GitHub Secrets (or your local environment)
CLIENT_ID = os.environ.get('REDDIT_CLIENT_ID')
CLIENT_SECRET = os.environ.get('REDDIT_CLIENT_SECRET')
USER_AGENT = 'python:lore_archivist:v2.0 (by /u/LoreBot)'

TARGET_SUBREDDITS = ['eldenringlore', 'EldenRingLoreTalk']
OUTPUT_FILE = 'lore_data.json'

# Search terms to find deep lore beyond just "top posts"
SEARCH_QUERIES = [
    'flair:"Lore Theory"', 
    'flair:"Speculation"', 
    'flair:"Analysis"', 
    'title:timeline',
    'title:"deep dive"'
]

# Categorization Buckets
LORE_TOPICS = {
    "The Outer Gods & Cosmos": ["greater will", "frenzied flame", "formless mother", "fell god", "dark moon", "astel", "fallingstar", "void", "stars"],
    "The Empyreans & Demigods": ["ranni", "miquella", "malenia", "radahn", "rykard", "morgott", "mohg", "godwyn", "messmer", "gloam-eyed", "trina"],
    "History & Factions": ["numen", "nox", "eternal city", "marika", "radagon", "golden order", "erdtree", "crucible", "misbegotten", "albinauric"],
    "Death & Destined Death": ["godskin", "black flame", "maliketh", "destined death", "deathroot", "fia", "those who live in death"],
    "Dragons & Beasts": ["placidusax", "gransax", "fortissax", "lansseax", "bayle", "farum azula", "beastman", "serosh"]
}

def get_reddit():
    return praw.Reddit(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        user_agent=USER_AGENT
    )

def scrape_and_save():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: Reddit API credentials not found in environment variables.")
        return

    reddit = get_reddit()
    seen_ids = set()
    all_posts = []

    print(f"--- Starting Deep Dive Scrape ---")

    for sub_name in TARGET_SUBREDDITS:
        subreddit = reddit.subreddit(sub_name)
        print(f"Scanning r/{sub_name}...")

        # 1. Get Top Posts (Month) to keep content fresh
        for post in subreddit.top(time_filter='month', limit=100):
            process_post(post, all_posts, seen_ids)

        # 2. Get Specific Flair/Search terms (All Time) for the deep archives
        for query in SEARCH_QUERIES:
            # Syntax='cloudsearch' is safer for advanced queries
            try:
                for post in subreddit.search(query, sort='top', time_filter='year', limit=50, syntax='cloudsearch'):
                    process_post(post, all_posts, seen_ids)
            except Exception as e:
                print(f"Skipping query '{query}' due to error: {e}")

    # Save to JSON for the frontend
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_posts, f, indent=2)
    
    print(f"Done! Saved {len(all_posts)} discussions to '{OUTPUT_FILE}'.")

def process_post(submission, collection, seen_ids):
    if submission.id in seen_ids:
        return
    
    # Filter: Must be at least 150 chars and have some upvotes
    if submission.stickied or submission.score < 10 or len(submission.selftext) < 150:
        return

    seen_ids.add(submission.id)

    # Determine Category
    best_topic = "General Lore"
    text_content = (submission.title + " " + submission.selftext).lower()
    
    # Simple keyword scoring
    for topic, keywords in LORE_TOPICS.items():
        if any(k in text_content for k in keywords):
            best_topic = topic
            break

    post_data = {
        "title": submission.title,
        "url": submission.url,
        "score": submission.score,
        "subreddit": submission.subreddit.display_name,
        "body": submission.selftext,
        "category": best_topic,
        "scraped_at": datetime.now().isoformat(),
        "comments": []
    }

    # Fetch top comment (just one for the preview card)
    try:
        submission.comments.replace_more(limit=0)
        top_comments = submission.comments.list()
        if top_comments:
            # Sort manually to be safe
            top_comments.sort(key=lambda x: x.score, reverse=True)
            best_comment = top_comments[0]
            
            # Only include if it's substantial
            if len(best_comment.body) > 50:
                post_data["comments"].append({
                    "author": str(best_comment.author),
                    "body": best_comment.body
                })
    except Exception:
        pass # Skip comments if errors occur (e.g. strict moderation)
    
    collection.append(post_data)

if __name__ == "__main__":
    scrape_and_save()