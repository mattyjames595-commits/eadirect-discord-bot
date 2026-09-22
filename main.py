import requests
import json
import os

# --- CONFIGURATION ---
TARGET_HANDLE = "futdonk"
# Direct public JSON endpoint for the account
API_URL = f"https://api.fxtwitter.com/{TARGET_HANDLE}"

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

KEYWORDS = ["6pm"]
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

def send_to_discord(tweet_text, tweet_link, media_url):
    embed = {
        "title": f"New @{TARGET_HANDLE} Post",
        "description": tweet_text,
        "url": tweet_link,
        "color": 16711680,
        "fields": [
            {"name": "Original Post", "value": f"[View on X]({tweet_link})", "inline": False}
        ]
    }
    
    if media_url:
        embed["image"] = {"url": media_url}

    payload = {"embeds": [embed]}
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    
    if response.status_code == 204:
        print("Successfully posted to Discord!")
    else:
        print(f"Failed to post to Discord. Status code: {response.status_code}")

def main():
    print(f"Checking @{TARGET_HANDLE} timeline...")
    last_seen = load_last_seen()
    
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(API_URL, headers=headers)
    
    if response.status_code != 200:
        print(f"API returned status code: {response.status_code}")
        return

    data = response.json()
    
    # Extract tweets safely from the response
    tweets = []
    if "tweets" in data:
        tweets = data["tweets"]
    elif "user" in data and "tweets" in data["user"]:
        tweets = data["user"]["tweets"]
    elif "tweet" in data:
        tweets = [data["tweet"]]

    if not tweets:
        print("No timeline tweets available in current payload response.")
        return

    new_seen = list(last_seen)
    found_new = false_flag = False

    for tweet in reversed(tweets):
        tweet_id = str(tweet.get("id"))
        
        if tweet_id in last_seen:
            continue
            
        tweet_text = tweet.get("text", "")
        tweet_link = tweet.get("url", f"https://twitter.com/{TARGET_HANDLE}")
        
        media_url = None
        media = tweet.get("media", {})
        photos = media.get("photos", [])
        if photos:
            media_url = photos[0].get("url")

        full_text = tweet_text.lower()
        if any(kw.lower() in full_text for kw in KEYWORDS):
            print(f"Match found! Sending to Discord...")
            send_to_discord(tweet_text, tweet_link, media_url)
        else:
            print(f"Skipped (keyword mismatch): {tweet_text[:30]}...")
            
        new_seen.append(tweet_id)
        found_new = True

    if found_new:
        save_last_seen(new_seen)
        print("State updated successfully.")
    else:
        print("No new posts found.")

if __name__ == "__main__":
    main()
