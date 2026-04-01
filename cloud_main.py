import pandas as pd
from playwright.sync_api import sync_playwright
from twilio.rest import Client
import traceback

from config import *
from ai_utils import *

from scrapers.wellfound import scrape_wellfound
from scrapers.indeed import scrape_indeed
from scrapers.hirist import scrape_hirist
from scrapers.remotive import scrape_remotive
from scrapers.remoteok import scrape_remoteok
from scrapers.yc_jobs import scrape_yc

client = Client(ACCOUNT_SID, AUTH_TOKEN)
results = []

def safe_run(func, *args):
    try:
        print(f"▶ Running {func.__name__}")
        func(*args)
    except Exception as e:
        print(f"❌ Failed: {func.__name__}")
        traceback.print_exc()

def run():
    resume_text = load_resume_text(RESUME_PATH)
    resume_embedding = get_embedding(resume_text)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        safe_run(scrape_wellfound, page, KEYWORDS, results)
        safe_run(scrape_indeed, page, KEYWORDS, LOCATIONS, results, parse_posted_time)
        safe_run(scrape_hirist, page, results)

        browser.close()

    safe_run(scrape_remotive, results)
    safe_run(scrape_remoteok, results)
    safe_run(scrape_yc, results)

    df = pd.DataFrame(results)
    df.drop_duplicates(inplace=True)

    df["Score"] = df["Role"].apply(lambda x: ai_match_score(resume_embedding, x))
    df.sort_values(by="Score", ascending=False, inplace=True)

    top_jobs = df.head(50)
    top_jobs.to_csv("data/jobs.csv", index=False)

    message = "🔥 Top Jobs:\n\n"

    for _, job in top_jobs.iterrows():
        message += f"{job['Company']} - {job['Role']}\n{job['Link']}\n\n"

    message = message[:1500]

    client.messages.create(
        from_=FROM_WHATSAPP,
        body=message,
        to=TO_WHATSAPP
    )

    print("✅ Done!")

if __name__ == "__main__":
    run()