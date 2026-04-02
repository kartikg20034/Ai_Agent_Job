import pandas as pd
from twilio.rest import Client
import traceback
import re

from config import *
from ai_utils import *

# Scrapers
from scrapers.internshala import scrape_internshala
from scrapers.letsintern import scrape_letsintern
from scrapers.adzuna import scrape_adzuna
from scrapers.remotive import scrape_remotive
from scrapers.remoteok import scrape_remoteok
from scrapers.yc_jobs import scrape_yc

client = Client(ACCOUNT_SID, AUTH_TOKEN)


# ---------------- SAFE RUN ----------------
def safe_run(func, *args):
    try:
        print(f"▶️ Running {func.__name__}")
        func(*args)
    except Exception:
        print(f"❌ Failed: {func.__name__}")
        traceback.print_exc()


# ---------------- FILTERS ----------------
def is_relevant(text):
    skills = ["python", "java", "backend", "ai", "ml", "spring"]
    return any(s in str(text).lower() for s in skills)


def is_entry_level(text):
    keywords = ["intern", "fresher", "junior", "entry", "0-1", "associate"]
    return any(k in str(text).lower() for k in keywords)


def extract_salary_value(text):
    text = str(text).lower()

    match = re.search(r'₹\s?(\d{4,6})', text)
    if match:
        return int(match.group(1))

    match = re.search(r'(\d+)\s?lpa', text)
    if match:
        return (int(match.group(1)) * 100000) // 12

    return 0


def process_source(results, resume_embedding, name):
    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results)

    if "Role" not in df.columns:
        return pd.DataFrame()

    df["Score"] = df["Role"].apply(lambda x: ai_match_score(resume_embedding, x))

    df = df[df["Role"].apply(is_relevant)]
    df = df[df["Role"].apply(is_entry_level)]

    df["Salary"] = df["Role"].apply(extract_salary_value)

    df = df[(df["Salary"] >= 20000) | (df["Salary"] == 0)]

    df = df.sort_values(by="Score", ascending=False).head(20)

    print(f"✅ {name}: {len(df)} jobs")

    return df


# ---------------- MAIN ----------------
def run():
    print("🚀 Cloud Job Agent...")

    resume = load_resume_text(RESUME_PATH)
    emb = get_embedding(resume)

    final = []

    for func, name in [
        (scrape_internshala, "Internshala"),
        (scrape_letsintern, "LetsIntern"),
        (scrape_adzuna, "Adzuna"),
        (scrape_remotive, "Remotive"),
        (scrape_remoteok, "RemoteOK"),
        (scrape_yc, "YC")
    ]:
        res = []
        safe_run(func, res)
        df = process_source(res, emb, name)
        if not df.empty:
            final.append(df)

    final_df = pd.concat(final, ignore_index=True)
    final_df.to_csv("data/jobs.csv", index=False)

    print("📊 Total:", len(final_df))

    # WhatsApp
    msg = "🔥 Top Jobs:\n\n"

    for _, j in final_df.head(20).iterrows():
        msg += f"{j['Company']} - {j['Role']}\n{j['Link']}\n\n"

    try:
        client.messages.create(
            from_=FROM_WHATSAPP,
            body=msg[:1500],
            to=TO_WHATSAPP
        )
        print("📩 Sent")
    except:
        print("⚠️ WhatsApp failed")


if __name__ == "__main__":
    run()