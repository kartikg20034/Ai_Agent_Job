import os
from dotenv import load_dotenv
from openai import OpenAI
import numpy as np
from pypdf import PdfReader

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY")
)

def load_resume_text(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text


def get_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text[:3000]
    )
    return response.data[0].embedding


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def ai_match_score(resume_emb, job_text):
    job_emb = get_embedding(job_text)
    return cosine_similarity(resume_emb, job_emb)


def parse_posted_time(text):
    text = text.lower()

    if "hour" in text or "just" in text:
        return 0
    elif "day" in text:
        return int(text.split()[0])
    elif "week" in text:
        return int(text.split()[0]) * 7
    return 999