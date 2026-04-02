from playwright.sync_api import sync_playwright

from scrapers.linkedin import scrape_linkedin
from scrapers.wellfound import scrape_wellfound
from scrapers.indeed_local import scrape_indeed_local

results = []

KEYWORDS = ["Python Developer", "AI Engineer", "Backend Developer"]
LOCATIONS = ["Remote", "Bangalore", "Hyderabad", "Gurugram"]


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir="session",
            headless=False
        )

        page = browser.new_page()

        # 🔐 LOGIN (LinkedIn only)
        print("👉 Login to LinkedIn once")
        page.goto("https://www.linkedin.com")
        input("Press ENTER after login...")

        # 🔵 LINKEDIN
        scrape_linkedin(page, KEYWORDS, LOCATIONS, results)

        # 🟣 WELLFOUND
        scrape_wellfound(page, KEYWORDS, results)

        # 🌐 INDEED
        scrape_indeed_local(page, KEYWORDS, LOCATIONS, results)

        print(f"\n📊 Total jobs collected: {len(results)}\n")

        # Print sample
        for job in results[:20]:
            print(job)

        browser.close()


if __name__ == "__main__":
    run()