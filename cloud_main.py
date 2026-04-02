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
def safe_run(func, name):
    results = []

    try:
        print(f"▶️ Running {name}")
        func(results)

        if not results:
            return {"status": "EMPTY", "data": None}

        return {"status": "SUCCESS", "data": results}

    except Exception:
        print(f"❌ {name} crashed")
        traceback.print_exc()
        return {"status": "FAILED", "data": None}


# ---------------- FILTERS ----------------

def is_relevant(text):
    skills = ["python", "java", "backend", "ai", "ml", "spring"]
    return any(s in str(text).lower() for s in skills)


def is_entry_level(text):
    keywords = ["intern", "fresher", "junior", "entry", "associate", "0-1"]
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


# ---------------- PROCESS SOURCE ----------------

def process_source(results, resume_embedding, name):
    try:
        df = pd.DataFrame(results)

        # ❌ bad structure
        if df.empty or "Role" not in df.columns:
            return {"status": "BAD_DATA", "df": None}

        df = df[df["Role"].notna()]

        if df.empty:
            return {"status": "BAD_DATA", "df": None}

        # 🧠 scoring
        df["Score"] = df["Role"].apply(lambda x: ai_match_score(resume_embedding, x))

        # 🎯 filters
        df = df[df["Role"].apply(is_relevant)]
        df = df[df["Role"].apply(is_entry_level)]

        if df.empty:
            return {"status": "FILTERED_OUT", "df": None}

        # 💰 salary
        df["Salary"] = df["Role"].apply(extract_salary_value)
        df = df[(df["Salary"] >= 20000) | (df["Salary"] == 0)]

        if df.empty:
            return {"status": "FILTERED_OUT", "df": None}

        df = df.sort_values(by="Score", ascending=False).head(20)

        return {"status": "SUCCESS", "df": df}

    except Exception:
        return {"status": "FAILED", "df": None}


# ---------------- MAIN ----------------

def run():
    print("🚀 Cloud Job Agent...")

    resume = load_resume_text(RESUME_PATH)
    emb = get_embedding(resume)

    final_dfs = []
    report = {}

    sources = [
        (scrape_internshala, "Internshala"),
        (scrape_letsintern, "LetsIntern"),
        (scrape_adzuna, "Adzuna"),
        (scrape_remotive, "Remotive"),
        (scrape_remoteok, "RemoteOK"),
        (scrape_yc, "YC")
    ]

    for func, name in sources:
        run_result = safe_run(func, name)

        if run_result["status"] == "FAILED":
            report[name] = "❌ FAILED"
            continue

        if run_result["status"] == "EMPTY":
            report[name] = "⚠️ NO JOBS"
            continue

        process_result = process_source(run_result["data"], emb, name)
        status = process_result["status"]

        if status == "SUCCESS":
            df = process_result["df"]
            final_dfs.append(df)
            report[name] = f"✅ {len(df)} jobs"

        elif status == "BAD_DATA":
            report[name] = "⚠️ BAD DATA"

        elif status == "FILTERED_OUT":
            report[name] = "⚠️ FILTERED OUT"

        else:
            report[name] = "❌ FAILED"

    # ---------------- REPORT ----------------
    print("\n📊 SCRAPER REPORT:")
    for k, v in report.items():
        print(f"{k}: {v}")

    if not final_dfs:
        print("❌ No valid jobs from any source")
        return

    # ---------------- FINAL DATA ----------------
    final_df = pd.concat(final_dfs, ignore_index=True)
    final_df = final_df.sort_values(by="Score", ascending=False)

    final_df.to_csv("data/jobs.csv", index=False)

    print(f"\n✅ Final jobs collected: {len(final_df)}")

    # ---------------- WHATSAPP ----------------
    message = "🔥 Top Jobs:\n\n"

    for _, job in final_df.head(20).iterrows():
        message += f"{job['Company']} - {job['Role']}\n"
        message += f"{job['Link']}\n\n"

    message += "\n📊 Report:\n"
    for k, v in report.items():
        message += f"{k}: {v}\n"

    try:
        client.messages.create(
            from_=FROM_WHATSAPP,
            body=message[:1500],
            to=TO_WHATSAPP
        )
        print("📩 WhatsApp sent!")
    except Exception:
        print("⚠️ WhatsApp failed (ignored)")


if __name__ == "__main__":
    run()