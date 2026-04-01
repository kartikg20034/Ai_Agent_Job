import requests

def scrape_remotive(results):
    data = requests.get("https://remotive.com/api/remote-jobs").json()

    for job in data["jobs"][:30]:
        results.append({
            "Platform": "Remotive",
            "Company": job["company_name"],
            "Role": job["title"],
            "Link": job["url"]
        })