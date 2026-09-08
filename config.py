import os

# WhatsApp API Base URLs
WA_VERIFY_URL = "https://web.whatsapp.com/checkcode"

# Cooldown settings (in seconds)
COOLDOWN_MINUTES = 1  

# Proxy format expected in proxy.txt: ip:port:username:password
# For SOCKS5, the format is usually the same. 
# Set PROXY_TYPE to 'socks5' if you are using SOCKS5 proxies.
PROXY_TYPE = "socks5" # Change this to "socks5" if needed

PROXY_FILE_PATH = os.path.join(os.path.dirname(__file__), "proxy.txt")

# Local state file to track last successful request
STATE_FILE = os.path.join(os.path.dirname(__file__), "wa_state.json")
