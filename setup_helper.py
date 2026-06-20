#!/usr/bin/env python3
import urllib.request
import urllib.error
import json
import sys

# Force UTF-8 encoding on stdout for Windows compatibility
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def make_request(url, data=None, headers=None):
    if headers is None:
        headers = {}
    
    req_data = None
    if data is not None:
        req_data = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
        
    req = urllib.request.Request(url, data=req_data, headers=headers, method='POST' if data else 'GET')
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = response.read().decode('utf-8')
            return response.status, json.loads(res_data)
    except urllib.error.HTTPError as e:
        try:
            err_data = e.read().decode('utf-8')
            err_json = json.loads(err_data)
            return e.code, err_json
        except Exception:
            return e.code, {"error": e.reason}
    except Exception as e:
        return 0, {"error": str(e)}

def main():
    print("==================================================")
    print("   WhatsApp GitHub Notifier Setup & Test Tool")
    print("==================================================")
    print("\nThis helper will connect to your Green-API account,")
    print("list your groups to find the Group ID, and send a test message.")
    print("Please make sure you registered on https://green-api.com")
    print("and scanned the QR code with your WhatsApp app first.\n")

    # Get Green-API credentials
    try:
        id_instance = input("Enter your Green-API idInstance (e.g. 1101123456): ").strip()
        if not id_instance:
            print("idInstance cannot be empty.")
            return

        api_token = input("Enter your Green-API apiTokenInstance: ").strip()
        if not api_token:
            print("apiTokenInstance cannot be empty.")
            return
    except KeyboardInterrupt:
        print("\nAborted.")
        return

    # 1. Fetch Chats
    print("\nFetching chats from Green-API...")
    url_chats = f"https://api.green-api.com/waInstance{id_instance}/getChats/{api_token}"
    
    status, response = make_request(url_chats)
    
    if status != 200:
        print(f"❌ Error fetching chats (Status {status}):")
        print(json.dumps(response, indent=2))
        print("\nPlease make sure:")
        print("1. Your idInstance and apiTokenInstance are correct.")
        print("2. Your WhatsApp instance status in the Green-API console is 'Authorized'.")
        return

    # Filter for groups
    groups = []
    for chat in response:
        # In Green-API, chat type is 'group' or ID contains @g.us
        chat_id = chat.get("id", "")
        chat_type = chat.get("type", "")
        chat_name = chat.get("name", "Unknown Group Name")
        
        if chat_type == "group" or "@g.us" in chat_id:
            groups.append({
                "id": chat_id,
                "name": chat_name
            })

    if not groups:
        print("\n⚠️ No WhatsApp groups found in your active chats!")
        print("Tip: If you just created a new group, send at least one message inside the group")
        print("from your phone, wait 1 minute, and run this script again.")
        return

    # Add search query to filter groups
    try:
        search_query = input("Enter a search term to filter your groups (or press Enter to list all): ").strip().lower()
    except KeyboardInterrupt:
        print("\nAborted.")
        return

    filtered_groups = []
    if search_query:
        for g in groups:
            if search_query in g['name'].lower() or search_query in g['id'].lower():
                filtered_groups.append(g)
    else:
        filtered_groups = groups

    if not filtered_groups:
        print(f"\n⚠️ No groups matched the search term '{search_query}'.")
        return

    print("\n==================================================")
    print("            FOUND WHATSAPP GROUPS")
    print("==================================================")
    for idx, group in enumerate(filtered_groups, 1):
        print(f"{idx}. Name: {group['name']}")
        print(f"   ID  : {group['id']}\n")
    print("==================================================")

    # 2. Select Group and send test message
    try:
        selection = input(f"Select a group number (1-{len(filtered_groups)}) or paste a Group ID: ").strip()
        if not selection:
            return

        target_group_id = None
        # Check if selection is numeric and within range
        if selection.isdigit():
            idx = int(selection) - 1
            if 0 <= idx < len(filtered_groups):
                target_group_id = filtered_groups[idx]['id']
                group_name = filtered_groups[idx]['name']
            else:
                print("Invalid number selection.")
                return
        else:
            # Assume they pasted the ID directly
            target_group_id = selection
            group_name = "Custom Group ID"

        confirm_test = input(f"Send a test message to '{group_name}'? (y/n): ").strip().lower()
        if confirm_test != 'y':
            print("Setup helper finished without sending a test message.")
            return

        # Send test message
        test_msg = "🦊 בוט העדכונים של גיטהאב מוכן לפעולה! קבוצה זו תתחיל לקבל עדכונים שוטפים בכל פעם שנעלה קוד חדש."
        url_send = f"https://api.green-api.com/waInstance{id_instance}/sendMessage/{api_token}"
        payload = {
            "chatId": target_group_id,
            "message": test_msg
        }

        print("\nSending test message...")
        status, response = make_request(url_send, payload)

        if status == 200:
            print("\n✅ Test message sent successfully!")
            print("Check your WhatsApp group to verify it arrived!")
            print("\n--------------------------------------------------")
            print("             WHAT TO DO NEXT:")
            print("--------------------------------------------------")
            print("1. Go to your GitHub repository: athlete-poster-automation")
            print("2. Navigate to Settings -> Secrets and variables -> Actions")
            print("3. Add the following New Repository Secrets:")
            print(f"   • GREEN_API_ID_INSTANCE : {id_instance}")
            print(f"   • GREEN_API_TOKEN       : {api_token}")
            print(f"   • GREEN_API_GROUP_ID   : {target_group_id}")
            print("   • GEMINI_API_KEY       : (Your Google Gemini API Key from AI Studio)")
            print("\n4. Copy the '.github' folder and 'notify.py' into the root")
            print("   of your repository, commit, and push!")
            print("--------------------------------------------------")
        else:
            print(f"\n❌ Failed to send test message (Status {status}):")
            print(json.dumps(response, indent=2))

    except KeyboardInterrupt:
        print("\nAborted.")

if __name__ == "__main__":
    main()
