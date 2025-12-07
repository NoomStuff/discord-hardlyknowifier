# Discord hardlyknowifier

This script looks in a Discord channel for any words ending with `er`, `ur`, `ure`, & `or` and automatically replies with the classic
**“<word>? I hardly know ’er!”**
response on your account. Being funny has never been easier!
Robust, highly customisable and of course... ridiculously overengineered

## ⭐ Features

* Robust detection system so the joke *(almost)* always makes sense
* Edit `triggers.txt` to change what gets replied to
* Edit `ignored.txt` to change what gets ignored
* Option ignore your own messages
* Handles rate-limits

---

## 📦 Setup

Download the folder, and run `hardlyknowifier.py`.
You need Python 3 installed, no extra dependencies.

The first time you run the script, it will ask you for:

1. **Your Discord token**
2. **A Discord Channel ID**
3. **Whether to ignore your own messages**

These are stored in `config.txt`. Rerun the script after the file is made.

> **Important:**
> Your Discord token gives full access to your account.
> **Do NOT share, upload or commit it anywhere else.**
> [How to get your Discord token](https://www.youtube.com/watch?v=5SRwnLYdpJs)

## ⚙️ How It Works

The script will automatically reply if:

1. It contains at least one word ending in a trigger 
2. The word is *not* blacklisted (filters out slurs)
3. The word is *not* in `ignored.txt`
3. The word is long enough to make sense
4. The letter before the trigger is not a vowel
5. The bot isn’t responding to itself

It also works with any casing, if it has an **s** at the end, and even if the message has multiple words that get triggered.

---

## 🙏 Notes

Having a bot using your account is against Discords TOS and not allowed by most servers, so probably keep it to you and some friends, or use at your own risk.

`config.txt` has your Discord token. So be extremely careful when sharing the project folder.

You are free to use the project however you want *(just try not to annoy people too much lol)*, it would be appreciated if you would provide credit when modifying, redistributing or showcasing my work.
