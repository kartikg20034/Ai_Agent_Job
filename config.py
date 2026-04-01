import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
FROM_WHATSAPP = os.getenv("TWILIO_FROM")
TO_WHATSAPP = os.getenv("TWILIO_TO")

KEYWORDS = ["Python Developer", "Java Backend", "AI Engineer", "Spring Boot"]
LOCATIONS = ["Remote", "Gurugram", "Bengaluru", "Hyderabad"]

RESUME_PATH = "data/resume.pdf"