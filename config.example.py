import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cold-email-agent"))
from config import SENDER_EMAIL, SENDER_NAME, YOUR_PHONE

ANTHROPIC_API_KEY = "sk-ant-..."   # paste your key from console.anthropic.com
GITHUB_USERNAME = "your-github-username"
GITHUB_PAGES_REPO = "demos"

LEADS_CSV = os.path.join(os.path.dirname(__file__), "..", "cold-email-agent", "leads_log.csv")
DEMOS_DIR = os.path.join(os.path.dirname(__file__), "demos")
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
