import requests

def scrape_remoteok(results):
    data = requests.get("https://remoteok.com/api").json()

    for job in data[1:30]:
        results.append({
            "Platform": "RemoteOK",
            "Company": job.get("company", ""),
            "Role": job.get("position", ""),
            "Link": job.get("url", "")
        })