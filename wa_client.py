import requests
import time
import json
import os
import urllib3
from config import WA_VERIFY_URL, STATE_FILE, COOLDOWN_MINUTES
from proxy_handler import get_proxy_list, get_best_proxy, get_phone_country_code

# Disable warnings for cleaner logs in Termux
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class WhatsAppClient:
    def __init__(self):
        self.proxies = get_proxy_list()
        self.last_request_time = self._load_state()

        # Use a session but allow it to close connections if needed
        self.session = requests.Session()

    def _load_state(self):
        """Load last request timestamp from local state file."""
        if not os.path.exists(STATE_FILE):
            return 0
        try:
            with open(STATE_FILE, 'r') as f:
                data = json.load(f)
                return data.get('last_request', 0)
        except (json.JSONDecodeError, IOError):
            return 0

    def _save_state(self):
        """Save current timestamp to local state file."""
        data = {'last_request': time.time()}
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(data, f)
        except IOError:
            pass 

    def _is_cooldown_active(self):
        """Check if we are in the cooldown period."""
        elapsed = time.time() - self.last_request_time
        if elapsed < (COOLDOWN_MINUTES * 60):
            return True
        return False

    def _get_proxy_for_number(self, phone_number):
        proxy_dict = get_best_proxy(self.proxies, phone_number)

        # Ensure the proxy URL is correctly formatted for requests
        base_url = proxy_dict['url']
        if not base_url.startswith('http'):
            base_url = 'http://' + base_url

        return {
            "http": base_url,
            "https": base_url
        }

    def send_code(self, phone_number, country_name="US"):
        """
        Sends the OTP request to WhatsApp via SMS.
        Returns True if successful, False otherwise.
        """
        if self._is_cooldown_active():
            remaining = (COOLDOWN_MINUTES * 60) - (time.time() - self.last_request_time)
            print(f"[INFO] Cooldown active. Please wait. Last request was {remaining:.0f} seconds ago.")
            return False

        proxy = self._get_proxy_for_number(phone_number)
        clean_num = phone_number.lstrip('+')

        # Payload for WhatsApp Checkcode API
        # method='sms' ensures we get an SMS, not a voice call
        payload = {
            "id": clean_num,
            "method": "sms",  # <--- Explicitly SMS
            "code": "",
            "cc": country_name,
            "lang": "en",
            "lgn": True
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "WhatsApp/2.23.15 Android/11 (Google Pixel 6)" # Realistic UA
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"[INFO] Attempt {attempt + 1}/{max_retries}: Sending SMS to {phone_number} via proxy {proxy['https']}")

                # Use verify=False to bypass SSL cert issues in Termux/Proxy
                # timeout is critical to prevent hanging
                response = self.session.post(
                    WA_VERIFY_URL, 
                    data=payload, 
                    headers=headers, 
                    proxies=proxy, 
                    timeout=10, # Reduced timeout for quicker failure detection
                    verify=False
                )

                if response.status_code == 200:
                    res_json = response.json()

                    # WhatsApp API usually returns {'code': '123456', 'status': 200} or similar
                    if res_json.get('code') or res_json.get('status') == 200:
                        print(f"[SUCCESS] Code requested successfully for {phone_number}. Country Code: {country_name}")
                        self.last_request_time = time.time()
                        self._save_state()

                        # Show the code if WhatsApp returns it immediately (some proxies/api do)
                        returned_code = res_json.get('code', 'Sent')
                        print(f"[INFO] Status: {res_json.get('status')} - Code: {returned_code}")
                        return True
                    else:
                        state = res_json.get('state', '')
                        status = res_json.get('status')

                        if 'unavailable' in str(state).lower() or 'red' in str(res_json).lower():
                            print(f"[ERROR] WhatsApp Unavailable (Red) for {phone_number}. Try again later.")
                            return False
                        elif 'recently connected' in str(res_json).lower() or status == 429:
                            print(f"[INFO] Recently connected / Too many requests for {phone_number}. Retrying soon.")
                            self.last_request_time = time.time() - 30 
                            return False
                        else:
                            print(f"[WARN] Unknown state for {phone_number}: {res_json}")
                            return True

                else:
                    print(f"[ERROR] HTTP Error: {response.status_code} for {phone_number}. Response: {response.text[:100]}")
                    if attempt < max_retries - 1:
                        continue # Retry
                    return False

            except requests.exceptions.SSLError as e:
                print(f"[SSL] SSL Error (Attempt {attempt+1}/{max_retries}): {e}")
                time.sleep(1) 
                if attempt == max_retries - 1:
                    return False

            except requests.exceptions.Timeout as e:
                print(f"[TIMEOUT] Read timed out (Attempt {attempt+1}/{max_retries}): {e}")
                time.sleep(1)
                if attempt == max_retries - 1:
                    return False

            except requests.exceptions.ConnectionError as e:
                print(f"[CONN] Connection Error (Attempt {attempt+1}/{max_retries}): {e}")
                time.sleep(1)
                if attempt == max_retries - 1:
                    return False

            except Exception as e:
                print(f"[EXC] Unexpected Exception: {e}")
                # Clear cooldown slightly on unexpected errors to allow retry
                self.last_request_time = time.time() - 50 
                return False

        return True

    def verify_code(self, phone_number, code):
        """Verifies the OTP code."""
        print(f"[INFO] Verifying code {code} for {phone_number}...")

        proxy = self._get_proxy_for_number(phone_number)
        clean_num = phone_number.lstrip('+')

        payload = {
            "id": clean_num,
            "code": str(code), # Ensure code is string
            "method": "sms"
        }

        try:
            response = self.session.post(WA_VERIFY_URL, data=payload, proxies=proxy, timeout=10)
            if response.status_code == 200:
                res_json = response.json()
                if res_json.get('status') == 200 or res_json.get('code'):
                    print(f"[SUCCESS] Code {code} verified successfully for {phone_number}.")
                    return True
            print(f"[ERROR] Code verification failed for {phone_number}. Status: {response.status_code}, Response: {response.text}")
            return False
        except Exception as e:
            print(f"[EXC] Exception verifying code: {e}")
            return False

    def get_account_transfer_code(self):
        """
        Simulates waiting for and capturing the account transfer code.
        """
        print("\n--- Account Transfer Phase ---")
        print("Please open WhatsApp on your phone.")
        input("Press Enter when you have received the account transfer code on your new device/app...")

        print("[SUCCESS] Account transfer confirmed. Proceeding to next account creation...")
        return True
