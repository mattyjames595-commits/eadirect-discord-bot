import feedparser
import requests
import json
import os
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
RSS_URL = "https://rsshub.app/twitter/user/EADirect"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")  # Paste your webhook URL here if not using secrets
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
    with open(LAST_SEEN_FILE, "w") as f:
        json.dump(seen_list[-50:], f)

def extract_image_and_text(raw_summary):
    """Extracts clean text and the first image URL from RSS HTML content."""
    soup = BeautifulSoup(raw_summary, "html.parser")
    
    # Find the first image if present in the tweet
    img_tag = soup.find("img")
    image_url = img_tag["src"] if img_tag else None
    
    # Clean up HTML tags for the text description
    clean_text = soup.get_text(separator="\n").strip()
    return clean_text, image_url

def send_to_discord(title, link, raw_summary):
    clean_description, image_url = extract_image_and_text(raw_summary)
    
    embed = {
        "title": "New @EADirect Tweet",
        "description": clean_description if clean_description else title,
        "url": link,
        "color": 16711680,  # Red accent color
        "fields": [
            {"name": "Original Post", "value": f"[View on X]({link})", "inline": False}
        ]
    }
    
    # Attach image directly so it renders as a picture in Discord
    if image_url:
        embed["image"] = {"url": image_url}

    payload = {"embeds": [embed]}
    
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if response.status_code == 204:
        print(f"Successfully posted to Discord with image/text.")
    else:
        print(f"Failed to post to Discord. Status code: {response.status_code}, Response: {response.text}")

def main():
    print("Checking RSS feed for @EADirect...")
    last_seen = load_last_seen()
    
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("No entries found or feed is currently rate-limited.")
        return

    new_seen = list(last_seen)
    found_new = False

    for entry in reversed(feed.entries):
        entry_id = entry.get("id") or entry.get("link")
        
        if entry_id in last_seen:
            continue
            
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        link = entry.get("link", "")
        
        # Combine text for keyword matching
        full_text = f"{title} {summary}".lower()
        
        # Check keyword filter
        if any(kw.lower() in full_text for kw in KEYWORDS):
            print(f"Match found! Sending to Discord...")
            send_to_discord(title, link, summary)
            
        new_seen.append(entry_id)
        found_new = True

    if found_new:
        save_last_seen(new_seen)
        print("State updated successfully.")
    else:
        print("No new posts to process.")

if __name__ == "__main__":
    main()
