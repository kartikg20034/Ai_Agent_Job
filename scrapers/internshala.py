import requests
from bs4 import BeautifulSoup

def scrape_internshala(results):
    print("🇮🇳 Internshala...")

    url = "https://internshala.com/internships/software-development-internship"
    html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).text
    soup = BeautifulSoup(html, "html.parser")

    cards = soup.select(".individual_internship")[:30]

    for c in cards:
        try:
            results.append({
                "Platform": "Internshala",
                "Company": c.select_one(".company_name").text.strip(),
                "Role": c.select_one(".profile").text.strip() + " internship fresher",
                "Link": "https://internshala.com" + c.select_one("a")["href"]
            })
        except:
            continue