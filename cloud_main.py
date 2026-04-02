import pandas as pd
from twilio.rest import Client
import traceback
import re
import time  # ✅ built-in

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


# ---------------- SAFE RUN (WITH TIMING) ----------------
def safe_run(func, name):
    results = []
    start = time.time()

    try:
        print(f"\n▶️ Running {name}...")

        func(results)

        duration = round(time.time() - start, 2)

        print(f"⏱ {name}: {duration}s")
        print(f"📦 {name} raw jobs: {len(results)}")

        if not results:
            return {"status": "EMPTY", "data": None, "time": duration, "count": 0}

        return {
            "status": "SUCCESS",
            "data": results,
            "time": duration,
            "count": len(results)
        }

    except Exception:
        duration = round(time.time() - start, 2)
        print(f"❌ {name} crashed after {duration}s")
        traceback.print_exc()

        return {"status": "FAILED", "data": None, "time": duration, "count": 0}


# ---------------- FILTERS ----------------

def is_not_senior(text):
    text = str(text).lower()
    senior = ["senior", "lead", "manager", "principal", "staff", "architect"]
    return not any(k in text for k in senior)


def is_relevant(text):
    skills = ["python", "java", "developer", "engineer", "backend", "ai"]
    return any(s in str(text).lower() for s in skills)


def fresher_bonus(text):
    text = str(text).lower()
    fresher = ["intern", "junior", "fresher", "entry", "graduate", "trainee"]
    return 0.3 if any(k in text for k in fresher) else 0


def extract_salary_value(text):
    text = str(text).lower()

    match = re.search(r'₹\s?(\d{4,6})', text)
    if match:
        return int(match.group(1))

    match = re.search(r'(\d+)\s?lpa', text)
    if match:
        return (int(match.group(1)) * 100000) // 12

    return 0


# ---------------- PROCESS ----------------

def process_source(results, emb, name):
    try:
        df = pd.DataFrame(results)

        if df.empty or "Role" not in df.columns:
            return {"status": "BAD_DATA", "df": None}

        df = df[df["Role"].notna()]

        if df.empty:
            return {"status": "BAD_DATA", "df": None}

        # AI score
        df["Score"] = df["Role"].apply(lambda x: ai_match_score(emb, x))

        # remove senior
        df = df[df["Role"].apply(is_not_senior)]

        # basic relevance
        df = df[df["Role"].apply(is_relevant)]

        if df.empty:
            return {"status": "FILTERED_OUT", "df": None}

        # salary (optional)
        df["Salary"] = df["Role"].apply(extract_salary_value)

        # boost fresher
        df["Score"] += df["Role"].apply(fresher_bonus)

        df = df.sort_values(by="Score", ascending=False)

        # fallback if too strict
        if df.empty:
            df = pd.DataFrame(results).head(10)

        df = df.head(20)

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

        report[name] = {
            "status": run_result["status"],
            "time": run_result["time"],
            "raw": run_result["count"],
            "final": 0
        }

        if run_result["status"] != "SUCCESS":
            continue

        process_result = process_source(run_result["data"], emb, name)

        if process_result["status"] == "SUCCESS":
            df = process_result["df"]
            final_dfs.append(df)
            report[name]["final"] = len(df)
        else:
            report[name]["status"] = process_result["status"]

    # ---------------- REPORT ----------------
    print("\n📊 SCRAPER REPORT:")
    for name, info in report.items():
        print(
            f"{name}: {info['status']} | "
            f"⏱ {info['time']}s | "
            f"📦 raw: {info['raw']} | "
            f"✅ final: {info['final']}"
        )

    if not final_dfs:
        print("❌ No jobs found")
        return

    final_df = pd.concat(final_dfs, ignore_index=True)
    final_df = final_df.sort_values(by="Score", ascending=False)

    final_df.to_csv("data/jobs.csv", index=False)

    print(f"\n✅ Final jobs: {len(final_df)}")

    # ---------------- WHATSAPP ----------------
    msg = "🔥 Top Fresher Jobs:\n\n"

    for _, j in final_df.head(20).iterrows():
        msg += f"{j['Company']} - {j['Role']}\n{j['Link']}\n\n"

    try:
        client.messages.create(
            from_=FROM_WHATSAPP,
            body=msg[:1500],
            to=TO_WHATSAPP
        )
        print("📩 WhatsApp sent!")
    except:
        print("⚠️ WhatsApp failed")


if __name__ == "__main__":
    run()