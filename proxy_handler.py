import re
import requests
from config import PROXY_FILE_PATH, PROXY_TYPE

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
                        "proxy_type": PROXY_TYPE
                    })
    except FileNotFoundError:
        print(f"Warning: {PROXY_FILE_PATH} not found. Using default or first proxy.")

    return proxies

def get_country_from_username(username):
    """Extracts the last 2 characters of the username as country code."""
    match = re.search(r'([a-zA-Z]{2})$', username)
    if match:
        return match.group(1).lower()
    return "us"

def get_phone_country_code(phone_number):
    """Extracts the country code from a phone number string."""
    if not phone_number:
        return None

    clean_num = phone_number.lstrip('+')

    # Common country codes mapping
    code_map = {
        '1': 'us',   # USA/Canada
        '7': 'ru',   # Russia
        '20': 'eg',  # Egypt
        '30': 'gr',  # Greece
        '31': 'nl',  # Netherlands
        '33': 'fr',  # France
        '34': 'es',  # Spain
        '39': 'it',  # Italy
        '40': 'ro',  # Romania
        '41': 'ch',  # Switzerland
        '44': 'gb',  # UK
        '48': 'pl',  # Poland
        '49': 'de',  # Germany
        '52': 'mx',  # Mexico
        '55': 'br',  # Brazil
        '60': 'my',  # Malaysia
        '61': 'au',  # Australia
        '62': 'id',  # Indonesia
        '63': 'ph',  # Philippines
        '64': 'nz',  # New Zealand
        '65': 'sg',  # Singapore
        '81': 'jp',  # Japan
        '82': 'kr',  # South Korea
        '84': 'vn',  # Vietnam
        '86': 'cn',  # China
        '90': 'tr',  # Turkey
        '91': 'in',  # India
        'ua': 'ua',  # Ukraine
        'pe': 'pe',  # Peru
    }

    for code in sorted(code_map.keys(), key=lambda x: len(x), reverse=True):
        if str(code).isdigit() and clean_num.startswith(str(code)):
            return code_map[str(code)]

    return "us"

def get_best_proxy(proxies, phone_number):
    """Selects a proxy whose country matches the phone number's country."""
    phone_country = get_phone_country_code(phone_number)

    for proxy in proxies:
        if proxy['country'].lower() == phone_country.lower():
            return proxy

    if proxies:
        return proxies[0]

    return {"ip": "127.0.0.1", "port": "8080", "username": "", "password": "", "country": phone_country, "proxy_type": PROXY_TYPE}

def get_requests_proxies(proxy_dict):
    """Converts proxy dict to requests library format."""
    ptype = proxy_dict['proxy_type'].lower()
    base_url = f"{ptype}://"

    if proxy_dict['username']:
        base_url += f"{proxy_dict['username']}:{proxy_dict['password']}"

    base_url += f"@{proxy_dict['ip']}:{proxy_dict['port']}"

    return {
        "http": base_url,
        "https": base_url
    }
