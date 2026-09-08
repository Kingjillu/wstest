import re
import requests
from config import PROXY_FILE_PATH

def get_proxy_list():
    """Reads proxy.txt and returns a list of proxy dictionaries."""
    proxies = []
    try:
        with open(PROXY_FILE_PATH, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # Format: ip:port:username:password
                parts = line.split(':')
                if len(parts) >= 4:
                    ip, port, username, password = parts[0], parts[1], parts[2], parts[3]

                    # Extract country code from username (e.g., abc.....ua -> ua)
                    country_code = get_country_from_username(username)

                    proxies.append({
                        "ip": ip,
                        "port": port,
                        "username": username,
                        "password": password,
                        "country": country_code,
                        "url": f"http://{username}:{password}@{ip}:{port}"
                    })
    except FileNotFoundError:
        print(f"Warning: {PROXY_FILE_PATH} not found. Using default or first proxy.")

    return proxies

def get_country_from_username(username):
    """Extracts the last 2 characters of the username as country code."""
    # Example: abc.....ua -> ua, abc.....pe -> pe
    # Handle edge case where username might have dots before country
    match = re.search(r'([a-zA-Z]{2})$', username)
    if match:
        return match.group(1).lower()
    return "us" # Default to US

def get_phone_country_code(phone_number):
    """
    Extracts the country code from a phone number string.
    Handles formats like +11234567890 or 11234567890
    Returns the ISO 2-letter code for proxy matching.
    """
    if not phone_number:
        return None

    # Remove leading +
    clean_num = phone_number.lstrip('+')

    # Mapping common codes to ISO 2-letter codes for proxy matching
    # This is a simplified mapping. You can expand it as needed.
    code_map = {
        '1': 'us',   # USA/Canada
        '7': 'ru',   # Russia/Kazakhstan
        '20': 'eg',  # Egypt
        '30': 'gr',  # Greece
        '31': 'nl',  # Netherlands
        '32': 'be',  # Belgium
        '33': 'fr',  # France
        '34': 'es',  # Spain
        '39': 'it',  # Italy
        '40': 'ro',  # Romania
        '41': 'ch',  # Switzerland
        '43': 'at',  # Austria
        '44': 'gb',  # UK
        '48': 'pl',  # Poland
        '49': 'de',  # Germany
        '52': 'mx',  # Mexico
        '54': 'ar',  # Argentina
        '55': 'br',  # Brazil
        '60': 'my',  # Malaysia
        '61': 'au',  # Australia
        '62': 'id',  # Indonesia
        '63': 'ph',  # Philippines
        '64': 'nz',  # New Zealand
        '65': 'sg',  # Singapore
        '66': 'th',  # Thailand
        '81': 'jp',  # Japan
        '82': 'kr',  # South Korea
        '84': 'vn',  # Vietnam
        '86': 'cn',  # China
        '90': 'tr',  # Turkey
        '91': 'in',  # India
        '92': 'pk',  # Pakistan
        '93': 'af',  # Afghanistan
        '94': 'lk',  # Sri Lanka
        '98': 'ir',  # Iran
        'ua': 'ua',  # Ukraine
        'pe': 'pe',  # Peru
    }

    # Check for multi-digit codes (2 or 3 digits) first to avoid conflicts
    # e.g., if country is 62, we don't want it to match just '6' if a single-digit map existed
    for code in sorted(code_map.keys(), key=lambda x: len(x), reverse=True):
        if str(code).isdigit() and clean_num.startswith(str(code)):
            return code_map[str(code)]

    # Fallback
    return "us"

def get_best_proxy(proxies, phone_number):
    """Selects a proxy whose country matches the phone number's country."""
    phone_country = get_phone_country_code(phone_number)

    # Try to find exact match first
    for proxy in proxies:
        if proxy['country'].lower() == phone_country.lower():
            return proxy

    # Fallback to any available proxy
    if proxies:
        return proxies[0]

    return {"ip": "127.0.0.1", "port": "8080", "username": "", "password": "", "country": phone_country, "url": f"http://{phone_number}@127.0.0.1:8080"}
