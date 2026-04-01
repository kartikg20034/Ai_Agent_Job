import pandas as pd
from playwright.sync_api import sync_playwright
from twilio.rest import Client

from config import *
from ai_utils import *
from scrapers.linkedin import scrape_linkedin
from scrapers.wellfound import scrape_wellfound
from scrapers.indeed import scrape_indeed

client = Client(ACCOUNT_SID, AUTH_TOKEN)
results = []


def score_job(job, resume_embedding):
    score = 0

    ai_score_val = ai_match_score(resume_embedding, job["Role"])
    score += ai_score_val * 10

    if job["Days_Ago"] <= 1:
        score += 3

    if job["Platform"] == "Wellfound":
        score += 4

    return score


def send_whatsapp(top_jobs):
    message = "🔥 Top AI-Matched Jobs:\n\n"

    for job in top_jobs:
        message += f"{job['Company']} - {job['Role']}\n"
        message += f"{job['Platform']} | {job['Posted']}\n"
        message += f"{job['Link']}\n\n"

    client.messages.create(
        from_=FROM_WHATSAPP,
        body=message,
        to=TO_WHATSAPP
    )


def run():
    resume_text = load_resume_text(RESUME_PATH)
    resume_embedding = get_embedding(resume_text)

    with sync_playwright() as p:

        # 🔥 Persistent session (NO LOGIN NEEDED AFTER FIRST TIME)
        browser = p.chromium.launch_persistent_context(
            user_data_dir="session",
            headless=False,
            slow_mo=500
        )

        page = browser.new_page()

        # First time → you login manually
        page.goto("https://www.linkedin.com")
        input("👉 First run: login manually, then press ENTER...")

        scrape_linkedin(page, KEYWORDS, LOCATIONS, results, parse_posted_time)
        scrape_wellfound(page, KEYWORDS, results)
        scrape_indeed(page, KEYWORDS, LOCATIONS, results, parse_posted_time)

        browser.close()

    df = pd.DataFrame(results)
    df.drop_duplicates(inplace=True)

    df["Score"] = df.apply(lambda x: score_job(x, resume_embedding), axis=1)
    df.sort_values(by="Score", ascending=False, inplace=True)

    df.to_csv("data/jobs.csv", index=False)

    top_jobs = df.head(5).to_dict("records")
    send_whatsapp(top_jobs)

    print("✅ DONE! Jobs saved + WhatsApp sent")


if __name__ == "__main__":
    run()