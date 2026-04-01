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
        "fresher", "graduate",
        "associate", "engineer i", "sde 1"
    ]
    return any(k in text for k in keywords)


def extract_salary_value(text):
    text = str(text).lower()

    match = re.search(r'₹\s?(\d{4,6})', text)
    if match:
        return int(match.group(1))

    match = re.search(r'(\d+)\s?lpa', text)
    if match:
        return (int(match.group(1)) * 100000) // 12

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
    if platform == "Wellfound":
        return 0.2
    if platform in ["YC", "Hirist"]:
        return 0.1
    return 0


def keyword_bonus(text):
    return 0.1 if "intern" in str(text).lower() else 0


# ---------------- PROCESS EACH SOURCE ----------------

def process_source(results, resume_embedding, source_name):
    if len(results) == 0:
        print(f"⚠️ {source_name}: no jobs scraped")
        return pd.DataFrame()

    df = pd.DataFrame(results)

    df.drop_duplicates(inplace=True)
    df.dropna(subset=["Role"], inplace=True)

    # 🧠 AI scoring
    df["Score"] = df["Role"].apply(lambda x: ai_match_score(resume_embedding, x))

    # 🎯 Filters
    df = df[df["Role"].apply(is_relevant)]
    df = df[df["Role"].apply(is_entry_level)]

    # 💰 Salary
    df["Salary_Value"] = df["Role"].apply(extract_salary_value)
    df["Salary_Label"] = df["Salary_Value"].apply(label_salary)

    df = df[(df["Salary_Value"] >= 20000) | (df["Salary_Value"] == 0)]

    # ⭐ Final scoring
    df["FinalScore"] = df["Score"]
    df["FinalScore"] += df["Platform"].apply(platform_bonus)
    df["FinalScore"] += df["Role"].apply(keyword_bonus)

    df = df.sort_values(by="FinalScore", ascending=False)

    df = df.head(20)

    print(f"✅ {source_name}: {len(df)} jobs selected")

    return df


# ---------------- MAIN ----------------

def run():
    print("🚀 Starting AI Job Agent...")

    resume_text = load_resume_text(RESUME_PATH)
    resume_embedding = get_embedding(resume_text)

    final_dfs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # WELLFOUND
        wf_results = []
        safe_run(scrape_wellfound, page, KEYWORDS, wf_results)
        wf_df = process_source(wf_results, resume_embedding, "Wellfound")
        if not wf_df.empty:
            final_dfs.append(wf_df)

        # INDEED
        indeed_results = []
        safe_run(scrape_indeed, page, KEYWORDS, LOCATIONS, indeed_results, parse_posted_time)
        indeed_df = process_source(indeed_results, resume_embedding, "Indeed")
        if not indeed_df.empty:
            final_dfs.append(indeed_df)

        # HIRIST
        hirist_results = []
        safe_run(scrape_hirist, page, hirist_results)
        hirist_df = process_source(hirist_results, resume_embedding, "Hirist")
        if not hirist_df.empty:
            final_dfs.append(hirist_df)

        browser.close()

    # REMOTIVE
    remotive_results = []
    safe_run(scrape_remotive, remotive_results)
    remotive_df = process_source(remotive_results, resume_embedding, "Remotive")
    if not remotive_df.empty:
        final_dfs.append(remotive_df)

    # REMOTEOK
    remoteok_results = []
    safe_run(scrape_remoteok, remoteok_results)
    remoteok_df = process_source(remoteok_results, resume_embedding, "RemoteOK")
    if not remoteok_df.empty:
        final_dfs.append(remoteok_df)

    # YC
    yc_results = []
    safe_run(scrape_yc, yc_results)
    yc_df = process_source(yc_results, resume_embedding, "YC")
    if not yc_df.empty:
        final_dfs.append(yc_df)

    if len(final_dfs) == 0:
        print("❌ No jobs collected")
        return

    # 🔥 Combine + global ranking
    final_df = pd.concat(final_dfs, ignore_index=True)
    final_df = final_df.sort_values(by="FinalScore", ascending=False)

    print(f"📊 Total final jobs: {len(final_df)}")

    final_df.to_csv("data/jobs.csv", index=False)

    # 📩 WhatsApp (top 20 only)
    message = "🔥 Top Entry-Level Jobs:\n\n"

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