#!/usr/bin/env python3
import os
import shutil
import subprocess
import requests
import sys
from nacl import encoding, public

# Force UTF-8 encoding on stdout for Windows compatibility
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


# 1. Load configuration from .env file
def load_env(env_path):
    secrets = {}
    if not os.path.exists(env_path):
        raise FileNotFoundError(f"Missing .env file at {env_path}")
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, val = line.split('=', 1)
            secrets[key.strip()] = val.strip()
    return secrets

def run_command(args, cwd):
    try:
        res = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Error running {' '.join(args)} in {cwd}: {e.stderr.strip()}")
        return None

def encrypt_secret(public_key: str, secret_value: str) -> str:
    """Encrypt a Unicode string using the public key."""
    pub_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(pub_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return encoding.Base64Encoder.encode(encrypted).decode("utf-8")

def set_github_secret(pat, repo_name, secret_name, secret_value):
    headers = {
        "Authorization": f"token {pat}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Get public key
    pk_url = f"https://api.github.com/repos/{repo_name}/actions/secrets/public-key"
    r = requests.get(pk_url, headers=headers)
    if r.status_code != 200:
        print(f"❌ Failed to get public key for {repo_name}. Status: {r.status_code}, Body: {r.text}")
        return False
        
    pk_data = r.json()
    key_id = pk_data["key_id"]
    public_key = pk_data["key"]
    
    # Encrypt secret
    encrypted_value = encrypt_secret(public_key, secret_value)
    
    # Upload secret
    upload_url = f"https://api.github.com/repos/{repo_name}/actions/secrets/{secret_name}"
    payload = {
        "encrypted_value": encrypted_value,
        "key_id": key_id
    }
    
    r_put = requests.put(upload_url, headers=headers, json=payload)
    if r_put.status_code in (201, 204):
        print(f"✅ Secret '{secret_name}' configured successfully in {repo_name}.")
        return True
    else:
        print(f"❌ Failed to upload secret '{secret_name}' to {repo_name}. Status: {r_put.status_code}, Body: {r_put.text}")
        return False

def main():
    base_dir = r"c:\Users\kesem\OneDrive\Desktop\KESEMITAY\CODE PROJECTS"
    env_path = os.path.join(base_dir, "notify updates", ".env")
    
    print("Reading secrets from .env...")
    try:
        secrets = load_env(env_path)
    except Exception as e:
        print(f"❌ Error loading .env file: {e}")
        return
        
    required_keys = ['GREEN_API_ID_INSTANCE', 'GREEN_API_TOKEN', 'GREEN_API_GROUP_ID', 'GEMINI_API_KEY', 'GITHUB_PAT']
    for k in required_keys:
        if not secrets.get(k):
            print(f"❌ Missing required key: {k} in .env file.")
            return

    pat = secrets['GITHUB_PAT']
    
    # Define repositories to configure
    repos = [
        {"dir": "notify updates", "name": "KESEMITAY/notify-updates"},
        {"dir": "athlete-poster-automation", "name": "KESEMITAY/athlete-poster-automation"},
        {"dir": "face-finder-auto", "name": "KESEMITAY/face-finder-auto"},
        {"dir": "whatsapp-task-manager", "name": "kesemitay/whatsapp-task-manager"},
        {"dir": "whatsapp-task-manager-bot1", "name": "KESEMITAY/whatsapp-task-manager-bot1"}
    ]

    source_workflow = os.path.join(base_dir, "notify updates", ".github", "workflows", "notify_whatsapp.yml")
    source_script = os.path.join(base_dir, "notify updates", "notify.py")

    print("\nStarting setup across all projects...\n")
    
    for repo in repos:
        repo_dir = os.path.join(base_dir, repo["dir"])
        repo_name = repo["name"]
        
        print(f"==================================================")
        print(f"Processing repository: {repo['dir']} ({repo_name})")
        print(f"==================================================")
        
        if not os.path.exists(repo_dir):
            print(f"⚠️ Directory {repo_dir} does not exist locally. Skipping file copy.")
            continue

        # 1. Copy workflow files (skip if it's the source repo itself)
        if repo["dir"] != "notify updates":
            target_workflow_dir = os.path.join(repo_dir, ".github", "workflows")
            os.makedirs(target_workflow_dir, exist_ok=True)
            
            shutil.copy2(source_workflow, os.path.join(target_workflow_dir, "notify_whatsapp.yml"))
            shutil.copy2(source_script, os.path.join(repo_dir, "notify.py"))
            print(f"📁 Copied workflow and notification script locally.")
            
            # Git add, commit, push
            print(f"🚀 Staging and pushing workflow files to GitHub...")
            run_command(["git", "add", ".github/workflows/notify_whatsapp.yml", "notify.py"], repo_dir)
            
            # Check if there are changes to commit
            status = run_command(["git", "status", "--porcelain"], repo_dir)
            if status:
                run_command(["git", "commit", "-m", "Add WhatsApp push notifier workflow"], repo_dir)
                push_res = run_command(["git", "push"], repo_dir)
                print(f"✅ Git files committed and pushed successfully.")
            else:
                print(f"ℹ️ No local file changes to commit.")
        else:
            print("ℹ️ Source files already configured in source repo.")

        # 2. Set repository secrets in GitHub via API
        print(f"🔑 Setting up secrets in GitHub repository {repo_name}...")
        set_github_secret(pat, repo_name, "GREEN_API_ID_INSTANCE", secrets["GREEN_API_ID_INSTANCE"])
        set_github_secret(pat, repo_name, "GREEN_API_TOKEN", secrets["GREEN_API_TOKEN"])
        set_github_secret(pat, repo_name, "GREEN_API_GROUP_ID", secrets["GREEN_API_GROUP_ID"])
        set_github_secret(pat, repo_name, "GEMINI_API_KEY", secrets["GEMINI_API_KEY"])
        print()

    print("==================================================")
    print("🎉 Setup finished successfully for all repositories!")
    print("==================================================")

if __name__ == "__main__":
    main()
