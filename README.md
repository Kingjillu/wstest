How to Run in Termux

    Install Python:

    pkg install python

    Install Dependencies:

    pip install requests

    Clone/Run: Save all files in a directory. Run the main script:

    python main.py

How it Bypasses Your Issues:

    Country Alignment: The proxy_handler.py reads the username part of your proxy (e.g., abc.....ua) and extracts the country code (ua). It then matches this with the country code of the phone number you input (e.g., +380... for Ukraine). This ensures you always use a proxy from the same region as the virtual number, reducing IP mismatch errors.
    Cooldown Management: The script maintains a local wa_state.json file. When you request an OTP, it checks the timestamp. If less

DIG8AA44FD0CB904A26797EA032C93AE714
