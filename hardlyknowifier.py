import json
import time
import re
from datetime import datetime
from http.client import HTTPSConnection
import os

CONFIG_FILE = "config.txt"
IGNORED_FILE = "ignored.txt"
TRIGGERS_FILE = "triggers.txt"

BLACKLIST = [
    re.compile(r"n(?:[^a-z0-9\s]*[i1!\|]){1}(?:[^a-z0-9\s]*[g6bq9G]){2}(?:[^a-z0-9\s]*[e3a@r])?(?:[^a-z0-9\s]*[r|a|ah|uh])?", re.IGNORECASE),
    re.compile(r"\bf\W*[a@4e3]\W*[gq96]\W*a?r?s?\b",re.IGNORECASE),
    re.compile(r"\bf(?:[^a-z0-9\s]*[a@4e3]){1}(?:[^a-z0-9\s]*[gq96]){1}(?:[^a-z0-9\s]*[a@4])?(?:[^a-z0-9\s]*[r]?)\b", re.IGNORECASE),
    re.compile(r"\bt\s*r\s*a\s*n\s*n\s*y\b", re.IGNORECASE)
]


def get_timestamp():
    return "[" + datetime.now().strftime("%H:%M:%S") + "]"


def read_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
            if len(lines) >= 2:
                token = lines[0].strip()
                channel = lines[1].strip()
                ignore_self = False
                if len(lines) >= 3:
                    ignore_self = lines[2].strip().lower() == "true"
                return token, channel, ignore_self
    except Exception as e:
        print(f"{get_timestamp()} Error reading config: {e}")
    return None, None, None


def write_config(token, channel_id, ignore_self):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(token + "\n" + channel_id + "\n" + str(ignore_self))


def configure():
    token = input("Discord token: ")
    channel = input("Discord channel ID: ")
    ignore_self = input("Ignore your own messages? (y/n): ").strip().lower() == "y"
    write_config(token, channel, ignore_self)
    print("Written config to config.txt, please rerun to start!")
    time.sleep(2)
    exit()


def get_connection():
    return HTTPSConnection("discordapp.com", 443)


def get_last_message(token, channel_id):
    try:
        headers = {"authorization": token, "host": "discordapp.com"}
        connection = get_connection()
        connection.request("GET", f"/api/v9/channels/{channel_id}/messages?limit=1", headers=headers)
        response = connection.getresponse()
        data = response.read().decode()
        connection.close()
    except Exception as e:
        print(f"{get_timestamp()} Network error getting messages: {e}")
        return None

    if not data:
        return None

    try:
        if response.status != 200:
            print(f"{get_timestamp()} Failed fetching messages ({response.status}): {data}")
            return None
        arr = json.loads(data)
        return arr[0] if arr else None
    except Exception as e:
        print(f"{get_timestamp()} Error parsing message response: {e}")
        return None


def send_message(token, channel_id, content):
    payload = json.dumps({"content": content})
    headers = {"content-type": "application/json", "authorization": token, "host": "discordapp.com"}

    while True:
        try:
            connection = get_connection()
            connection.request("POST", f"/api/v9/channels/{channel_id}/messages", payload, headers)
            response = connection.getresponse()
            body = response.read().decode()
            connection.close()
        except Exception as e:
            print(f"{get_timestamp()} Network error sending message: {e}")
            return False

        if response.status == 429:
            try:
                retry_after = json.loads(body).get("retry_after", 1)
            except Exception:
                retry_after = 1
            print(f"{get_timestamp()} Rate-limited. Retrying in {retry_after}s")
            time.sleep(retry_after + 0.05)
            continue

        if 199 < response.status < 300:
            print(f"{get_timestamp()} Sent: {content}")
            return True

        print(f"{get_timestamp()} Failed to send ({response.status}): {body}")
        return False


def load_list_file(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                return {line.strip().lower() for line in file if line.strip()}
        except Exception as e:
            print(f"{get_timestamp()} Error loading {filename}: {e}")
    return set()


def check_blacklist(word):
    for pattern in BLACKLIST:
        if pattern.search(word):
            return True
    return False


def main():
    token, channel, ignore_self = read_config()
    if not token or not channel:
        print(f"{get_timestamp()} No config was found. Running configuration setup.")
        configure()

    ignored = load_list_file(IGNORED_FILE)
    triggers = load_list_file(TRIGGERS_FILE)
    if not triggers:
        triggers = {"er"}

    print(f"{get_timestamp()} Checking latest messages.\nTriggers: {triggers}, Ignored: {ignored}\n\n")

    last_timestamp = None
    my_user_id = None

    while True:
        message = get_last_message(token, channel)
        if not message:
            time.sleep(1)
            continue

        message_timestamp = message.get("id")
        
        content = message.get("content") or ""
        author = message.get("author", {}).get("id")

        if message_timestamp == last_timestamp:
            time.sleep(1)
            continue
        last_timestamp = message_timestamp

        # get own user id, used for ignoring own messages
        if my_user_id is None:
            try:
                conn = get_connection()
                conn.request("GET", "/api/v9/users/@me", headers={"authorization": token})
                resp = conn.getresponse()
                data = resp.read().decode()
                conn.close()
                if resp.status == 200:
                    me = json.loads(data)
                    my_user_id = me.get("id")
                else:
                    print(f"{get_timestamp()} Failed to fetch @me ({resp.status}): {data}")
            except Exception as e:
                print(f"{get_timestamp()} Error fetching @me: {e}")

        # Ignore own messages if configured
        if ignore_self and author == my_user_id:
            print(f"{get_timestamp()} Found message by self, skipping.")
            time.sleep(1)
            continue

        # Avoid replying to bot message
        if "i hardly know 'er!" in content.lower():
            continue

        words = re.findall(r"\b\w+\b", content)
        replied = False
        skip_reasons = ""

        for word in words:
            word = word.lower()
            if word.endswith("s") and len(word) > 1:
                word = word[:-1]

            if check_blacklist(word):
                skip_reasons += f"'{word}' is blacklisted. "
                continue
            
            if word in ignored:
                skip_reasons += f"'{word}' is in ignored.txt. "
                continue

            for trigger in triggers:
                trigger = trigger.lower()

                if not word.endswith(trigger):
                    continue

                if len(word) <= len(trigger) + 1:
                    skip_reasons += f"'{word}' is too short. "
                    continue

                if word[-len(trigger)-1] in "aeiou":
                    skip_reasons += f"'{word}' has a vowel before '{trigger}'. "
                    continue


                print(f"{get_timestamp()} Found message with trigger '{trigger}', replying.")
                reply_text = f"{word.capitalize()}? I hardly know 'er!"
                sent_ok = send_message(token, channel, reply_text)
                if sent_ok:
                    replied = True
                else:
                    print(f"{get_timestamp()} Failed to send reply for: {word}")
                break 

        if not replied:
            if skip_reasons != "":
                print(f"{get_timestamp()} Found message didn't pass checks, skipping. {skip_reasons}")
            else:
                print(f"{get_timestamp()} Found message has no trigger, skipping.")

        time.sleep(1)


if __name__ == "__main__":
    main()
