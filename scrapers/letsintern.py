import requests
from bs4 import BeautifulSoup

def scrape_letsintern(results):
    print("🇮🇳 LetsIntern...")

    url = "https://www.letsintern.com/internships"
    html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).text
    soup = BeautifulSoup(html, "html.parser")

    cards = soup.select(".internship-card")[:30]

    for c in cards:
        try:
            title = c.select_one(".profile").text.strip()
            company = c.select_one(".company").text.strip()

            results.append({
                "Platform": "LetsIntern",
                "Company": company,
                "Role": title + " internship fresher",
                "Link": url
            })
        except:
            continue
        