import requests
import json
import os
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
# Target public mobile/alternative reader page which renders simple HTML without heavy JS walls
TARGET_HANDLE = "EADirect"
PAGE_URL = f"https://vxtwitter.com/{TARGET_HANDLE}"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL"  # Paste your Discord webhook URL here
KEYWORDS = []  # Change/add your keywords here (lowercase)
LAST_SEEN_FILE = "last_seen.json"

def load_last_seen():
    if os.path.exists(LAST_SEEN_FILE):
        try:
            with open(LAST_SEEN_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_last_seen(seen_list):
    # Keep the last 50 IDs to prevent the file from growing indefinitely
    with open(LAST_SEEN_FILE, "w") as f:
        json.dump(seen_list[-50:], f)

def send_to_discord(tweet_text, tweet_link, media_url):
    embed = {
        "title": f"New @{TARGET_HANDLE} Post Match",
        "description": tweet_text,
        "url": tweet_link,
        "color": 16711680,  # Red theme color
        "fields": [
            {"name": "Original Post", "value": f"[View on X]({tweet_link})", "inline": False}
        ]
    }
    
    # Attach image directly so it renders as a picture in Discord
    if media_url:
        embed["image"] = {"url": media_url}

    payload = {"embeds": [embed]}
    
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if response.status_code == 204:
        print(f"Successfully posted tweet to Discord!")
    else:
        print(f"Failed to post to Discord. Status code: {response.status_code}")

def main():
    print(f"Scraping timeline for @{TARGET_HANDLE} using BeautifulSoup...")
    last_seen = load_last_seen()
    
    # Custom User-Agent to mimic a standard browser request
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(PAGE_URL, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to fetch page. Status code: {response.status_code}")
        return

    # Pass HTML into BeautifulSoup for parsing
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Extract meta tags or article elements where preview wrappers store posts
    # Alternative front-ends store individual tweets neatly inside article blocks or meta descriptions
    posts = soup.find_all("div", class_="tweet-card") # or structural equivalent
    
    if not posts:
        # Fallback: parse open-graph meta tags if it loads as a single profile page card
        meta_desc = soup.find("meta", property="og:description")
        meta_image = soup.find("meta", property="og:image")
        
        if not meta_desc:
            print("Could not parse posts via BeautifulSoup.")
            return
            
        tweet_text = meta_desc.get("content", "")
        media_url = meta_image.get("content", "") if meta_image else None
        tweet_link = f"https://twitter.com/{TARGET_HANDLE}"
        
        # Use a pseudo-ID based on text content hash or link for state tracking
        tweet_id = str(hash(tweet_text))
        
        if tweet_id in last_seen:
            print("No new unique posts found.")
            return
            
        full_text = tweet_text.lower()
        if any(kw.lower() in full_text for kw in KEYWORDS):
            print(f"Match found! Sending to Discord...")
            send_to_discord(tweet_text, tweet_link, media_url)
            
        save_last_seen(last_seen + [tweet_id])
        return

    print(f"Found {len(posts)} posts to evaluate.")

if __name__ == "__main__":
    main()
