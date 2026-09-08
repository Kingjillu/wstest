import requests
import time
import json
import os # <-- Added missing import
from config import WA_VERIFY_URL, STATE_FILE, COOLDOWN_MINUTES
from proxy_handler import get_proxy_list, get_best_proxy, get_phone_country_code

class WhatsAppClient:
    def __init__(self):
        self.proxies = get_proxy_list()
        self.last_request_time = self._load_state()

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
            pass # Ignore if we can't write

    def _is_cooldown_active(self):
        """Check if we are in the cooldown period."""
        elapsed = time.time() - self.last_request_time
        if elapsed < (COOLDOWN_MINUTES * 60):
            return True
        return False

    def _get_proxy_for_number(self, phone_number):
        proxy_dict = get_best_proxy(self.proxies, phone_number)
        # Return requests-style proxies format
        return {
            "http": proxy_dict['url'],
            "https": proxy_dict['url']
        }

    def send_code(self, phone_number, country_name="US"):
        """
        Sends the OTP request to WhatsApp.
        Returns True if successful, False otherwise.
        """
        if self._is_cooldown_active():
            remaining = (COOLDOWN_MINUTES * 60) - (time.time() - self.last_request_time)
            print(f"Cooldown active. Please wait. Last request was {remaining:.0f} seconds ago.")
            return False

        proxy = self._get_proxy_for_number(phone_number)

        # Construct payload
        # WhatsApp web usually expects the number in E.164 format without +
        clean_num = phone_number.lstrip('+')

        payload = {
            "id": clean_num,
            "method": "sms",  # Can be 'whatsapp' or 'voice'
            "code": "",
            "cc": country_name,
            "lang": "en",
            "lgn": True
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-WA-Client-Id": "1.2345.67890" # Random client ID format
        }

        try:
            response = requests.post(WA_VERIFY_URL, data=payload, headers=headers, proxies=proxy, timeout=10)

            if response.status_code == 200:
                res_json = response.json()
                # WhatsApp often returns {'code': '...', 'state': 'ok'} or similar
                if res_json.get('code') or res_json.get('status') == 200:
                    print(f"Code requested successfully for {phone_number}. Country Code: {country_name}")
                    self.last_request_time = time.time()
                    self._save_state()
                    return True
                else:
                    # Check for specific errors
                    state = res_json.get('state', '')
                    status_code = res_json.get('status', 200)

                    if 'unavailable' in str(state).lower() or 'red' in str(res_json).lower():
                        print(f"WhatsApp Unavailable (Red) for {phone_number}. Try again later.")
                        return False
                    elif 'recently connected' in str(res_json).lower() or status_code == 429:
                        print(f"Recently connected / Too many requests for {phone_number}. Retrying soon.")
                        self.last_request_time = time.time() - 30 # Slightly earlier cooldown
                        return False
                    return True
            else:
                print(f"HTTP Error: {response.status_code} for {phone_number}")
                return False

        except Exception as e:
            print(f"Exception while sending code: {e}")
            return False

    def verify_code(self, phone_number, code):
        """Verifies the OTP code."""
        proxy = self._get_proxy_for_number(phone_number)
        clean_num = phone_number.lstrip('+')

        payload = {
            "id": clean_num,
            "code": code,
            "method": "sms"
        }

        try:
            response = requests.post(WA_VERIFY_URL, data=payload, proxies=proxy, timeout=10)
            if response.status_code == 200:
                res_json = response.json()
                if res_json.get('status') == 200 or res_json.get('code'):
                    print(f"Code {code} verified successfully for {phone_number}.")
                    return True
            print(f"Code verification failed for {phone_number}. Status: {response.status_code}")
            return False
        except Exception as e:
            print(f"Exception verifying code: {e}")
            return False

    def get_account_transfer_code(self):
        """
        Simulates waiting for and capturing the account transfer code.
        In a real Termux setup, you might hook into the notification or use whatsapp-web.js library.
        For this script, we assume the user inputs the code manually as per your description.
        """
        print("\n--- Account Transfer Phase ---")
        print("Please open WhatsApp on your phone.")
        input("Press Enter when you have received the account transfer code on your new device/app...")

        # In a full automation, this would read from a specific file or API endpoint
        # For now, we return a placeholder or allow user input if needed.
        print("Account transfer confirmed. Proceeding to next account creation...")
        return True
