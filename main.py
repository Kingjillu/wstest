import sys
import time
import os
from proxy_handler import get_proxy_list, get_phone_country_code
from wa_client import WhatsAppClient

def main():
    print("WhatsApp Account Creation System")
    print("-" * 30)

    # Initialize client
    client = WhatsAppClient()

    # Load all proxies
    all_proxies = get_proxy_list()
    if not all_proxies:
        print("No proxies found in proxy.txt. Please check the file.")
        return

    while True:
        print("\n--- New Account Creation ---")

        # 1. Input Phone Number
        phone_input = input("Enter Phone Number with Country Code (e.g., +380671234567): ").strip()
        if not phone_input.startswith('+'):
            phone_input = '+' + phone_input

        # Determine country code for proxy alignment
        phone_country_code = get_phone_country_code(phone_input)
        print(f"Detected Country Code: {phone_country_code}. Selecting appropriate proxy...")

        # 2. Request OTP
        print("Requesting OTP...")
        code_sent = client.send_code(phone_input, phone_country_code)

        if not code_sent:
            print("Could not request code. Please check your proxy or wait for cooldown.")
            retry = input("Do you want to retry? (y/n): ").lower()
            if retry == 'y':
                continue
            else:
                break

        # 3. Input OTP
        otp_input = input("Enter the OTP code received on your virtual number panel: ").strip()

        # 4. Verify OTP
        print(f"Verifying code {otp_input}...")
        is_verified = client.verify_code(phone_input, otp_input)

        if is_verified:
            print("\nWhatsApp Account Created Successfully in Work Profile!")

            # 5. Handle Account Transfer
            transfer_done = client.get_account_transfer_code()

            if transfer_done:
                print("Account transfer complete. Adding to phone apps.")

        else:
            print("Code verification failed. Please try again.")

        # Ask if user wants to create another account
        another = input("\nCreate another unlimited account? (y/n): ").lower()
        if another != 'y':
            print("Exiting system.")
            break

if __name__ == "__main__":
    main()
