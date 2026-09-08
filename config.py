import os

# WhatsApp API Base URLs
WA_VERIFY_URL = "https://web.whatsapp.com/checkcode"
WA_REGISTER_URL = "https://api.whatsapp.com/v2/register"
WA_CHECK_CODE_URL = "https://api.whatsapp.com/v2/check-code"

# Cooldown settings (in seconds)
COOLDOWN_MINUTES = 1  

# Proxy format expected in proxy.txt: ip:port:username:password
PROXY_FILE_PATH = os.path.join(os.path.dirname(__file__), "proxy.txt")

# Local state file to track last successful request
STATE_FILE = os.path.join(os.path.dirname(__file__), "wa_state.json")
