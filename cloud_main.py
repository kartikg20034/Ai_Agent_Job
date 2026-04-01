import pandas as pd
from playwright.sync_api import sync_playwright
from twilio.rest import Client
import traceback
import re

from config import *
from ai_utils import *

# Scrapers
from scrapers.wellfound import scrape_wellfound
from scrapers.indeed import scrape_indeed
from scrapers.hirist import scrape_hirist
from scrapers.remotive import scrape_remotive
from scrapers.remoteok import scrape_remoteok
from scrapers.yc_jobs import scrape_yc

client = Client(ACCOUNT_SID, AUTH_TOKEN)


# ---------------- SAFE RUN ----------------
def safe_run(func, *args):
    try:
        print(f"▶ Running {func.__name__}")
        func(*args)
    except Exception:
        print(f"❌ Failed: {func.__name__}")
        traceback.print_exc()


# ---------------- FILTERS ----------------

def is_relevant(text):
    text = str(text).lower()
    skills = ["python", "java", "backend", "ai", "ml", "spring", "api"]
    return any(s in text for s in skills)


def is_entry_level(text):
    text = str(text).lower()
    keywords = [
        "intern", "internship",
        "junior", "entry level",
        "0-1", "0 to 1", "1 year",
        "fresher", "graduate"
    ]
    return any(k in text for k in keywords)


def extract_salary_value(text):
    text = str(text).lower()

    # ₹ monthly
    match = re.search(r'₹\s?(\d{4,6})', text)
    if match:
        return int(match.group(1))

    # LPA → monthly
    match = re.search(r'(\d+)\s?lpa', text)
    if match:
        return (int(match.group(1)) * 100000) // 12

    # USD → INR approx
    match = re.search(r'\$(\d+)', text)
    if match:
        return int(match.group(1)) * 80

    return 0


def label_salary(val):
    if val == 0:
        return "Not specified"
    elif val >= 100000:
        return "High 💰"
    elif val >= 50000:
        return "Medium 💰"
    else:
        return "Low 💰"


def platform_bonus(platform):
    return 0.15 if platform == "Wellfound" else 0


def keyword_bonus(text):
    text = str(text).lower()
    return 0.1 if "intern" in text else 0


def balance_sources(df, max_per_source=10):
    return df.groupby("Platform").head(max_per_source).reset_index(drop=True)


# ---------------- MAIN ----------------

def run():
    print("🚀 Starting AI Job Agent...")

    resume_text = load_resume_text(RESUME_PATH)
    resume_embedding = get_embedding(resume_text)

    final_dfs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # ---------------- WELLFOUND ----------------
        wf_results = []
        safe_run(scrape_wellfound, page, KEYWORDS, wf_results)
        final_dfs.append(process_source(wf_results, resume_embedding, "Wellfound"))

        # ---------------- INDEED ----------------
        indeed_results = []
        safe_run(scrape_indeed, page, KEYWORDS, LOCATIONS, indeed_results, parse_posted_time)
        final_dfs.append(process_source(indeed_results, resume_embedding, "Indeed"))

        # ---------------- HIRIST ----------------
        hirist_results = []
        safe_run(scrape_hirist, page, hirist_results)
        final_dfs.append(process_source(hirist_results, resume_embedding, "Hirist"))

        browser.close()

    # ---------------- REMOTIVE ----------------
    remotive_results = []
    safe_run(scrape_remotive, remotive_results)
    final_dfs.append(process_source(remotive_results, resume_embedding, "Remotive"))

    # ---------------- REMOTEOK ----------------
    remoteok_results = []
    safe_run(scrape_remoteok, remoteok_results)
    final_dfs.append(process_source(remoteok_results, resume_embedding, "RemoteOK"))

    # ---------------- YC ----------------
    yc_results = []
    safe_run(scrape_yc, yc_results)
    final_dfs.append(process_source(yc_results, resume_embedding, "YC"))

    # 🔥 Combine all
    final_df = pd.concat(final_dfs, ignore_index=True)

    print(f"📊 Total final jobs: {len(final_df)}")

    # 💾 Save
    final_df.to_csv("data/jobs.csv", index=False)

    # 📩 WhatsApp (top 20 only to avoid spam)
    message = "🔥 Top Jobs (Multi-source):\n\n"

    top_jobs = final_df.head(20)

    for _, job in top_jobs.iterrows():
        message += f"{job['Company']} - {job['Role']}\n"
        message += f"💰 {job['Salary_Label']}\n"
        message += f"{job['Link']}\n\n"

    message = message[:1500]

    try:
        client.messages.create(
            from_=FROM_WHATSAPP,
            body=message,
            to=TO_WHATSAPP
        )
        print("📩 WhatsApp sent!")
    except Exception as e:
        print("⚠️ WhatsApp failed:", e)


if __name__ == "__main__":
    run()