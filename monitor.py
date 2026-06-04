import os
import requests
import base64
import json
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
GH_TOKEN = os.environ.get("GH_TOKEN")

REPO_NAME = "usiiusii/dhammacariya-results" 
FILE_PATH = "data.json"

TARGET_URLS = [
    "http://www.mahana.org.mm",
    "http://www.mora.gov.mm",
    "http://www.dra.gov.mm"
]

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

def update_github_json(new_links_data):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GH_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print("data.json ကို ရှာမတွေ့ပါ။")
            return

        file_info = response.json()
        sha = file_info['sha']
        
        content = base64.b64decode(file_info['content']).decode('utf-8')
        json_data = json.loads(content)

        updated = False

        # အထူးစာရင်းများ (Special Links)
        if "အထူးစာရင်းများ" not in json_data:
            json_data["အထူးစာရင်းများ"] = {"အထူးအောင်": "", "ဂုဏ်ထူးအောင်": ""}

        if "အထူးအောင်" in new_links_data:
            json_data["အထူးစာရင်းများ"]["အထူးအောင်"] = new_links_data["အထူးအောင်"]
            updated = True
        
        if "ဂုဏ်ထူးအောင်" in new_links_data:
            json_data["အထူးစာရင်းများ"]["ဂုဏ်ထူးအောင်"] = new_links_data["ဂုဏ်ထူးအောင်"]
            updated = True

        # ပြည်နယ်အားလုံးအတွက် လင့်ခ်များကို အလိုအလျောက် လိုက်ဖြည့်ခြင်း
        for state in json_data:
            if state == "အထူးစာရင်းများ":
                continue
                
            if "သုံးကျမ်း" in new_links_data:
                json_data[state]["ကျမ်းပြီး"] = new_links_data["သုံးကျမ်း"]
                updated = True
            if "နှစ်ကျမ်း" in new_links_data:
                json_data[state]["နှစ်ကျမ်းစွဲ"] = new_links_data["နှစ်ကျမ်း"]
                updated = True
            if "တစ်ကျမ်း" in new_links_data:
                json_data[state]["တစ်ကျမ်းစွဲ"] = new_links_data["တစ်ကျမ်း"]
                updated = True

        if updated:
            updated_content = json.dumps(json_data, indent=4, ensure_ascii=False).encode('utf-8')
            encoded_content = base64.b64encode(updated_content).decode('utf-8')

            payload = {
                "message": "Auto-updated Dhammacariya links (including Honors)",
                "content": encoded_content,
                "sha": sha
            }

            put_response = requests.put(url, headers=headers, json=payload)
            if put_response.status_code in [200, 201]:
                print("✅ GitHub JSON ကို အောင်မြင်စွာ Update လုပ်ပြီးပါပြီ။")
                send_telegram_message("✅ *Website တွင် အောင်စာရင်းလင့်ခ်များ အလိုအလျောက် Update လုပ်ပြီးပါပြီ!*")
            else:
                print("❌ GitHub Update လုပ်ရာတွင် Error ဖြစ်ပါသည်:", put_response.text)

    except Exception as e:
        print(f"❌ JSON Update Error: {e}")

def check_websites():
    print("စစ်ဆေးနေပါသည်...")
    links_to_update = {}
    found_any = False
    
    for url in TARGET_URLS:
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                links = soup.find_all('a', href=True)
                
                new_msgs = []
                for link in links:
                    href = link['href']
                    text = link.text.strip()
                    
                    if "drive.google.com" in href and ("ဓမ္မာစရိယ" in text or "အောင်စာရင်း" in text or "ဂုဏ်ထူး" in text or "အရှင်မြတ်" in text):
                        found_any = True
                        new_msgs.append(f"[{text}]({href})")
                        
                        # အထူးအောင် နှင့် ဂုဏ်ထူးအောင် စစ်ဆေးခြင်း
                        if "ပထမ" in text or "အရှင်မြတ်" in text or "အထူးအောင်" in text:
                            links_to_update["အထူးအောင်"] = href
                        elif "ဂုဏ်ထူး" in text:
                            links_to_update["ဂုဏ်ထူးအောင်"] = href
                        elif "သုံးကျမ်း" in text:
                            links_to_update["သုံးကျမ်း"] = href
                        elif "နှစ်ကျမ်း" in text:
                            links_to_update["နှစ်ကျမ်း"] = href
                        elif "တစ်ကျမ်း" in text:
                            links_to_update["တစ်ကျမ်း"] = href

                if new_msgs:
                    msg = f"🚨 *ဓမ္မာစရိယ အောင်စာရင်းလင့်ခ် တွေ့ရှိပါသည်!*\nWebsite: {url}\n\n"
                    for msg_link in new_msgs:
                        msg += f"🔗 {msg_link}\n\n"
                    send_telegram_message(msg)
                    
        except Exception as e:
            print(f"{url} သို့ ဝင်မရပါ။")

    if links_to_update:
        update_github_json(links_to_update)
    elif not found_any:
        print("အသစ်မတွေ့သေးပါ။")

if __name__ == "__main__":
    check_websites()
