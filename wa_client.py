import requests
import time
import json
import os
import urllib3
from config import WA_VERIFY_URL, STATE_FILE, COOLDOWN_MINUTES
from proxy_handler import get_proxy_list, get_best_proxy, get_requests_proxies

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class WhatsAppClient:
    def __init__(self):
        self.proxies = get_proxy_list()
        self.last_request_time = self._load_state()

    def _load_state(self):
        if not os.path.exists(STATE_FILE):
            return 0
        try:
            with open(STATE_FILE, 'r') as f:
                data = json.load(f)
                return data.get('last_request', 0)
        except (json.JSONDecodeError, IOError):
            return 0

    def _save_state(self):
        data = {'last_request': time.time()}
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(data, f)
        except IOError:
            pass 

    def _is_cooldown_active(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < (COOLDOWN_MINUTES * 60):
            return True
        return False

    def send_code(self, phone_number, country_name="US"):
        if self._is_cooldown_active():
            remaining = (COOLDOWN_MINUTES * 60) - (time.time() - self.last_request_time)
            print(f"[INFO] Cooldown active. Wait {remaining:.0f}s.")
            return False

        best_proxy = get_best_proxy(self.proxies, phone_number)
        proxies_dict = get_requests_proxies(best_proxy)

        clean_num = phone_number.lstrip('+')

        payload = {
            "id": clean_num,
            "method": "sms",
            "code": "",
            "cc": country_name,
            "lang": "en",
            "lgn": True
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "WhatsApp/2.23.15 Android/11"
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"[INFO] Attempt {attempt + 1}/{max_retries}: Sending SMS to {phone_number} via {proxies_dict['https']}")

                # verify=False helps with SSL EOF errors in Termux
                response = requests.post(
                    WA_VERIFY_URL, 
                    data=payload, 
                    headers=headers, 
                    proxies=proxies_dict, 
                    timeout=10,
                    verify=False
                )

                if response.status_code == 200:
                    res_json = response.json()
                    if res_json.get('code') or res_json.get('status') == 200:
                        print(f"[SUCCESS] Code sent successfully to {phone_number}.")
                        self.last_request_time = time.time()
                        self._save_state()
                        return True
                    else:
                        state = res_json.get('state', '')
                        if 'unavailable' in str(state).lower():
                            print(f"[ERROR] Unavailable for {phone_number}.")
                            return False
                        elif 'recently connected' in str(res_json).lower() or res_json.get('status') == 429:
                            self.last_request_time = time.time() - 30
                            return False
                        print(f"[WARN] State: {res_json}")
                        return True
                else:
                    print(f"[ERROR] HTTP Error {response.status_code} for {phone_number}")
                    if attempt < max_retries - 1:
                        continue
                    return False

            except requests.exceptions.SSLError as e:
                print(f"[SSL] SSL Error (Attempt {attempt+1}/{max_retries}): {e}")
                time.sleep(1) 
                if attempt == max_retries - 1:
                    return False

            except requests.exceptions.Timeout:
                print(f"[TIMEOUT] Timeout (Attempt {attempt+1}/{max_retries})")
                time.sleep(1)
                if attempt == max_retries - 1:
                    return False

            except Exception as e:
                print(f"[EXC] Unexpected: {e}")
                self.last_request_time = time.time() - 50 
                return False

        return True

    def verify_code(self, phone_number, code):
        print(f"[INFO] Verifying code {code} for {phone_number}...")
        best_proxy = get_best_proxy(self.proxies, phone_number)
        proxies_dict = get_requests_proxies(best_proxy)

        clean_num = phone_number.lstrip('+')

        payload = {
            "id": clean_num,
            "code": str(code),
            "method": "sms"
        }

        try:
            response = requests.post(WA_VERIFY_URL, data=payload, proxies=proxies_dict, timeout=10)
            if response.status_code == 200:
                res_json = response.json()
                if res_json.get('status') == 200 or res_json.get('code'):
                    print(f"[SUCCESS] Code {code} verified for {phone_number}.")
                    return True
            print(f"[ERROR] Verification failed for {phone_number}.")
            return False
        except Exception as e:
            print(f"[EXC] Verify exception: {e}")
            return False

    def get_account_transfer_code(self):
        print("\n--- Account Transfer Phase ---")
        print("Please open WhatsApp on your phone.")
        input("Press Enter when you have received the account transfer code on your new device/app...")
        print("[SUCCESS] Account transfer confirmed.")
        return True
