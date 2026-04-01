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


# 🔥 Safe runner (skip failing scrapers)
def safe_run(func, *args):
    try:
        print(f"▶ Running {func.__name__}")
        func(*args)
    except Exception as e:
        print(f"❌ Failed: {func.__name__}")
        traceback.print_exc()


# 🎯 Skill filter
def is_relevant(text):
    text = str(text).lower()
    skills = ["python", "java", "backend", "ai", "ml", "spring", "api"]
    return any(s in text for s in skills)


# 💰 Extract salary (monthly INR estimate)
def extract_salary_value(text):
    text = str(text).lower()

    # ₹ monthly
    match = re.search(r'₹\s?(\d{4,6})', text)
    if match:
        return int(match.group(1))

    # LPA → monthly
    match = re.search(r'(\d+)\s?lpa', text)
    if match:
        lpa = int(match.group(1))
        return (lpa * 100000) // 12

    # USD rough conversion
    match = re.search(r'\$(\d+)', text)
    if match:
        usd = int(match.group(1))
        return usd * 80

    return 0


# 💰 Label salary
def label_salary(val):
    if val == 0:
        return "Not specified"
    elif val >= 100000:
        return "High 💰"
    elif val >= 50000:
        return "Medium 💰"
    else:
        return "Low 💰"


def run():
    print("🚀 Starting AI Job Agent...")

    # 🧠 Resume embedding
    resume_text = load_resume_text(RESUME_PATH)
    resume_embedding = get_embedding(resume_text)

    all_results = []

    # 🌐 Browser scrapers
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        safe_run(scrape_wellfound, page, KEYWORDS, all_results)
        safe_run(scrape_indeed, page, KEYWORDS, LOCATIONS, all_results, parse_posted_time)
        safe_run(scrape_hirist, page, all_results)

        browser.close()

    # 🌍 API scrapers
    safe_run(scrape_remotive, all_results)
    safe_run(scrape_remoteok, all_results)
    safe_run(scrape_yc, all_results)

    print(f"📊 Total jobs scraped: {len(all_results)}")

    if len(all_results) == 0:
        print("❌ No jobs found")
        return

    # 📊 Convert to DataFrame
    df = pd.DataFrame(all_results)

    # 🧹 Clean
    df.drop_duplicates(inplace=True)
    df.dropna(subset=["Role"], inplace=True)

    # 🧠 AI scoring
    df["Score"] = df["Role"].apply(lambda x: ai_match_score(resume_embedding, x))

    # 🎯 Skill filtering
    df = df[df["Role"].apply(is_relevant)]

    # 💰 Salary extraction
    df["Salary_Value"] = df["Role"].apply(extract_salary_value)
    df["Salary_Label"] = df["Salary_Value"].apply(label_salary)

    # 🔥 Salary filter (≥ ₹20k OR unknown)
    df = df[(df["Salary_Value"] >= 20000) | (df["Salary_Value"] == 0)]

    # ⭐ Prefer jobs with salary
    df["HasSalary"] = df["Salary_Value"] > 0

    # 🔥 Final ranking
    df = df.sort_values(by=["HasSalary", "Score"], ascending=False)

    # 🎯 Final top 30 jobs
    final_jobs = df.head(30)

    final_jobs.to_csv("data/jobs.csv", index=False)

    print(f"✅ Final jobs saved: {len(final_jobs)}")

    # 📩 WhatsApp message
    message = "🔥 Top 30 AI Jobs:\n\n"

    for _, job in final_jobs.iterrows():
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