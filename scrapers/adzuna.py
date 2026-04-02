import requests

APP_ID = "e0988465"
APP_KEY = "9af8a0831c38271140148c6d38209159"


def scrape_adzuna(results):
    print("🌐 Adzuna (India Fresher Jobs)...")

    url = "https://api.adzuna.com/v1/api/jobs/in/search/1"

    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "results_per_page": 50,
        "what": "software engineer fresher OR python developer intern OR backend intern",
        "where": "India",
        "content-type": "application/json"
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        jobs = data.get("results", [])

        for job in jobs:
            try:
                title = job.get("title", "")
                company = job.get("company", {}).get("display_name", "Unknown")
                location = job.get("location", {}).get("display_name", "")
                link = job.get("redirect_url", "")

                # 💰 salary (if exists)
                salary_min = job.get("salary_min")
                salary_max = job.get("salary_max")

                salary_text = ""
                if salary_min and salary_max:
                    salary_text = f"₹{int(salary_min)} - ₹{int(salary_max)}"

                results.append({
                    "Platform": "Adzuna",
                    "Company": company,
                    "Role": f"{title} fresher intern {salary_text}",
                    "Link": link
                })

            except:
                continue

    except Exception as e:
        print("❌ Adzuna failed:", e)