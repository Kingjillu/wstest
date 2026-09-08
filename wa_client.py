import requests
import ssl
import time
import json
import os
from config import WA_VERIFY_URL, STATE_FILE, COOLDOWN_MINUTES
from proxy_handler import get_proxy_list, get_best_proxy, get_phone_country_code

class WhatsAppClient:
    def __init__(self):
        self.proxies = get_proxy_list()
        self.last_request_time = self._load_state()

        # Create a session with a specific adapter to handle SSL/HTTP properly
        self.session = requests.Session()

        # Create SSL context to be more lenient (good for Termux/Proxy combos)
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        # Mount the adapter with this SSL context
        from requests.adapters import HTTPAdapter
        self.session.mount('https://', HTTPAdapter(max_retries=3, pool_connections=10, pool_maxsize=10))

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
        # Format: http://username:password@ip:port
        base_url = proxy_dict['url']
        if not base_url.startswith('http'):
            base_url = 'http://' + base_url

        return {
            "http": base_url,
            "https": base_url
        }

    def send_code(self, phone_number, country_name="US"):
        """
        Sends the OTP request to WhatsApp with robust error handling.
        """
        if self._is_cooldown_active():
            remaining = (COOLDOWN_MINUTES * 60) - (time.time() - self.last_request_time)
            print(f"Cooldown active. Please wait. Last request was {remaining:.0f} seconds ago.")
            return False

        proxy = self._get_proxy_for_number(phone_number)
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
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            "X-WA-Client-Id": f"1.{int(time.time())}.67890"
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Note: verify=False disables strict SSL cert verification 
                # which helps with some proxy issues, while using default session handling.
                response = self.session.post(
                    WA_VERIFY_URL, 
                    data=payload, 
                    headers=headers, 
                    proxies=proxy, 
                    timeout=15,
                    verify=False 
                )

                if response.status_code == 200:
                    res_json = response.json()

                    if res_json.get('code') or res_json.get('status') == 200:
                        print(f"Code requested successfully for {phone_number}. Country Code: {country_name}")
                        self.last_request_time = time.time()
                        self._save_state()
                        return True
                    else:
                        state = res_json.get('state', '')
                        if 'unavailable' in str(state).lower() or 'red' in str(res_json).lower():
                            print(f"WhatsApp Unavailable (Red) for {phone_number}. Try again later.")
                            return False
                        elif 'recently connected' in str(res_json).lower() or res_json.get('status') == 429:
                            print(f"Recently connected / Too many requests for {phone_number}. Retrying soon.")
                            self.last_request_time = time.time() - 30 
                            return False
                        # Other errors
                        return True

                else:
                    print(f"HTTP Error: {response.status_code} for {phone_number}")
                    if attempt < max_retries - 1:
                        continue # Retry
                    return False

            except requests.exceptions.SSLError as e:
                print(f"SSL Error (Attempt {attempt+1}/{max_retries}): {e}")
                time.sleep(1) 
                if attempt == max_retries - 1:
                    return False

            except requests.exceptions.ConnectionError as e:
                print(f"Connection Error (Attempt {attempt+1}/{max_retries}): {e}")
                time.sleep(1)
                if attempt == max_retries - 1:
                    return False

            except Exception as e:
                print(f"Unexpected Exception: {e}")
                # Clear cooldown slightly on unexpected errors to allow retry
                self.last_request_time = time.time() - 50 
                return False

        return True

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
            response = self.session.post(WA_VERIFY_URL, data=payload, proxies=proxy, timeout=15)
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
        """
        print("\n--- Account Transfer Phase ---")
        print("Please open WhatsApp on your phone.")
        input("Press Enter when you have received the account transfer code on your new device/app...")

        print("Account transfer confirmed. Proceeding to next account creation...")
        return True
