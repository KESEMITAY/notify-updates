#!/usr/bin/env python3
import os
import json
import urllib.request
import urllib.error
import subprocess
import sys

# Force UTF-8 encoding on stdout for Windows compatibility
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def run_command(args):
    try:
        return subprocess.check_output(args, stderr=subprocess.STDOUT).decode('utf-8', errors='replace').strip()
    except Exception as e:
        return f"Error running command {' '.join(args)}: {str(e)}"

def get_git_diff(before, after):
    # Check if we can get a diff between the commits
    if not before or before == '0'*40 or before.startswith('000000'):
        # New branch or tag, diff the last commit
        return run_command(['git', 'diff', 'HEAD~1', 'HEAD'])
    return run_command(['git', 'diff', before, after])

def summarize_with_gemini(api_key, pusher_name, commits_info, files_changed, diff_content, repo_name):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    # Clean and limit diff content size to avoid overloading the API
    if diff_content and len(diff_content) > 6000:
        diff_content = diff_content[:6000] + "\n... [diff truncated for length] ..."

    # Constructing a detailed prompt in Hebrew to guide the translation/summary
    prompt = f"""
You are a friendly, cool developer bot named "אנדי" (Andy) notifying a two-person development team (קסם/Kesem and איתי/Itay) about a new push to their WhatsApp group for the repository '{repo_name}'.
Write a WhatsApp notification message. The entire message must be in HEBREW only.

CRITICAL INSTRUCTIONS FOR MESSAGE STRUCTURE:
The message MUST follow this exact format:

היי חברים כאן אנדי! [You can vary the greeting slightly but keep it short]
🔔 *עדכון חדש בגיטהאב!*

*מאת:* {pusher_name}

*השינויים שבוצעו*
-{repo_name}-
-[Explain the changes here in simple, clear Hebrew. Translate technical terms into simple concepts so anyone can understand.]

*קבצים ששונו/נוספו:*
-[List the changed/added files here. If there are none, write "אין" (None).]

[⚠️ Add specific recommendations (like "מומלץ לעשות git pull") here ONLY if there are specific warnings or recommendations needed. Otherwise omit this part.]

[Write a line break, then write a short, witty, or funny motivational developer quote/sentence to keep morale high. Keep it short and sharp.]

CRITICAL RULES:
1. GREETING & PUSHER TERMINOLOGY: Always state that "{pusher_name} ביצע פוש". Do NOT use the words "דחף" or "לדחוף" anywhere in the message. Always use the phrasing "ביצע פוש".
2. NO HAND EMOJIS: Do NOT use any hand emojis (such as 👋, 🖐️, ✋, ✍️, 👉, 👈, 👇, 👆, etc.) anywhere in the message.
3. EXPLAIN ONLY IN HEBREW: Do not use technical English jargon (like "refactor", "bugfix", "endpoint", "array") in the explanation. Translate them or explain them in simple Hebrew so that ANYONE (even a non-technical person) can easily understand what change was made.
4. Keep the message concise (max 1000 characters) to ensure readability on a phone screen.

Here are the details of the push:
- Pusher: {pusher_name}
- Commits:
{commits_info}
- Files changed:
{files_changed}
- Git diff:
{diff_content}

Return ONLY the final WhatsApp message text in Hebrew. Do not wrap in markdown or code blocks.
"""
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "maxOutputTokens": 1000,
            "temperature": 0.7
        }
    }
    
    req_data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res_data = response.read().decode('utf-8')
            res_json = json.loads(res_data)
            text = res_json['candidates'][0]['content']['parts'][0]['text']
            return text.strip()
    except Exception as e:
        print(f"⚠️ Gemini API failed: {e}")
        return None

def send_whatsapp_message(id_instance, token, group_id, message):
    url = f"https://api.green-api.com/waInstance{id_instance}/sendMessage/{token}"
    payload = {
        "chatId": group_id,
        "message": message
    }
    req_data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = response.read().decode('utf-8')
            res_json = json.loads(res_data)
            return True, res_json
    except Exception as e:
        return False, str(e)

def main():
    print("🚀 Starting GitHub Push WhatsApp Notifier...")
    
    # 1. Load configuration from environment
    id_instance = os.environ.get('GREEN_API_ID_INSTANCE')
    token = os.environ.get('GREEN_API_TOKEN')
    group_id = os.environ.get('GREEN_API_GROUP_ID')
    gemini_key = os.environ.get('GEMINI_API_KEY')
    
    if not id_instance or not token or not group_id:
        print("❌ Missing WhatsApp configuration. Please set GREEN_API_ID_INSTANCE, GREEN_API_TOKEN, and GREEN_API_GROUP_ID.")
        exit(1)
        
    # 2. Parse GitHub Event Data
    event_path = os.environ.get('GITHUB_EVENT_PATH')
    pusher_name = "מפתח בפרויקט"
    commits_info = ""
    files_changed = []
    before_sha = ""
    after_sha = ""
    
    # Get repository name dynamically
    repo_full_name = os.environ.get('GITHUB_REPOSITORY', '')
    if repo_full_name:
        repo_name = repo_full_name.split('/')[-1]
    else:
        # Fallback to local git repository folder name
        repo_toplevel = run_command(['git', 'rev-parse', '--show-toplevel'])
        if repo_toplevel and not repo_toplevel.startswith("Error"):
            repo_name = os.path.basename(repo_toplevel.strip())
        else:
            repo_name = "פרויקט"
    
    if event_path and os.path.exists(event_path):
        try:
            with open(event_path, 'r', encoding='utf-8') as f:
                event_data = json.load(f)
                
            raw_pusher = event_data.get('pusher', {}).get('name', '')
            if not raw_pusher and 'sender' in event_data:
                raw_pusher = event_data.get('sender', {}).get('login', '')
                
            if raw_pusher and ("kesem" in raw_pusher.lower() or "lulu" in raw_pusher.lower()):
                pusher_name = "קסם"
            else:
                pusher_name = "איתי"
            
            before_sha = event_data.get('before', '')
            after_sha = event_data.get('after', '')
            
            commits = event_data.get('commits', [])
            print(f"Found {len(commits)} commits in this push.")
            
            for c in commits:
                author = c.get('author', {}).get('name', '')
                msg = c.get('message', '').strip()
                commits_info += f"- {msg} (מאת: {author})\n"
                
                # Gather files changed
                files_changed.extend(c.get('added', []))
                files_changed.extend(c.get('modified', []))
                files_changed.extend(c.get('removed', []))
                
            # Keep unique files
            files_changed = sorted(list(set(files_changed)))
            
        except Exception as e:
            print(f"⚠️ Error parsing GITHUB_EVENT_PATH: {e}")
    else:
        print("⚠️ No GITHUB_EVENT_PATH found. Running in local test/fallback mode.")
        raw_pusher = run_command(['git', 'log', '-1', '--format=%an'])
        if raw_pusher and ("kesem" in raw_pusher.lower() or "lulu" in raw_pusher.lower()):
            pusher_name = "קסם"
        else:
            pusher_name = "איתי"
        before_sha = "HEAD~1"
        after_sha = "HEAD"
        commits_info = f"- {run_command(['git', 'log', '-1', '--format=%B'])}\n"
        
        # Git diff to find files
        files_str = run_command(['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'])
        files_changed = files_str.splitlines() if files_str else []

    files_changed_str = "\n".join([f"- {f}" for f in files_changed]) if files_changed else "- (אין קבצים ששונו)"
    
    # 3. Retrieve Git Diff
    diff_content = get_git_diff(before_sha, after_sha)
    
    # 4. Generate Message
    whatsapp_message = None
    if gemini_key:
        print("🤖 Generating summary message via Gemini API...")
        whatsapp_message = summarize_with_gemini(
            gemini_key, 
            pusher_name, 
            commits_info, 
            files_changed_str, 
            diff_content,
            repo_name
        )
        
    # Fallback message generator if Gemini failed or is not configured
    if not whatsapp_message:
        print("📝 Using template fallback for WhatsApp message...")
        whatsapp_message = (
            f"היי חברים כאן אנדי!\n"
            f"🔔 *עדכון חדש בגיטהאב!*\n\n"
            f"*מאת:* {pusher_name}\n\n"
            f"*השינויים שבוצעו*\n"
            f"-{repo_name}-\n"
            f"{commits_info}\n"
            f"*קבצים ששונו/נוספו:*\n"
            f"{files_changed_str}\n\n"
            f"⚠️ מומלץ לעשות `git pull` לפני שממשיכים לעבוד כדי למנוע התנגשויות!\n\n"
            f"💻 יאללה להמשיך להפגיז, הקוד לא ייכתב מעצמו!"
        )
        
    print("\n--- Message to Send ---")
    print(whatsapp_message)
    print("-----------------------\n")
    
    # 5. Send message via GreenAPI
    print("📤 Sending WhatsApp message to group...")
    success, response = send_whatsapp_message(id_instance, token, group_id, whatsapp_message)
    
    if success:
        print("✅ Message sent successfully!")
        print("Response:", json.dumps(response))
    else:
        print("❌ Failed to send WhatsApp message.")
        print("Error:", response)
        exit(1)

if __name__ == "__main__":
    main()
# Test trigger for WhatsApp notification
# Trigger Shmulik test
# Test Andy trigger
# Trigger formatting check




