import sys
import time
import os
from proxy_handler import get_proxy_list, get_phone_country_code
from wa_client import WhatsAppClient

def main():
    print("WhatsApp Account Creation System")
    print("-" * 30)

    client = WhatsAppClient()
    all_proxies = get_proxy_list()

    if not all_proxies:
        print("No proxies found in proxy.txt.")
        return

    while True:
        print("\n--- New Account Creation ---")

        phone_input = input("Enter Phone Number with Country Code (e.g., +380671234567): ").strip()
        if not phone_input.startswith('+'):
            phone_input = '+' + phone_input

        phone_country_code = get_phone_country_code(phone_input)
        print(f"[INFO] Detected Country Code: {phone_country_code}.")

        code_sent = client.send_code(phone_input, phone_country_code)

        if not code_sent:
            print("Could not request code.")
            retry = input("Do you want to retry? (y/n): ").lower()
            if retry == 'y':
                continue
            else:
                break

        otp_input = input("Enter the OTP code received on your virtual number panel: ").strip()

        is_verified = client.verify_code(phone_input, otp_input)

        if is_verified:
            print("\n[SUCCESS] WhatsApp Account Created Successfully!")
            client.get_account_transfer_code()

        else:
            print("Code verification failed.")

        another = input("\nCreate another unlimited account? (y/n): ").lower()
        if another != 'y':
            print("[INFO] Exiting system.")
            break

if __name__ == "__main__":
    main()
