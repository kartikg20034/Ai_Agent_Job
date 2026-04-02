def scrape_wellfound(page, keywords, results):
    print("🟣 Wellfound...")

    for keyword in keywords:
        url = f"https://wellfound.com/jobs?query={keyword}"
        page.goto(url)
        page.wait_for_timeout(5000)

        for _ in range(3):
            page.mouse.wheel(0, 4000)
            page.wait_for_timeout(2000)

        jobs = page.query_selector_all("div[data-testid='job-list-item']")

        for job in jobs[:25]:
            try:
                text = job.inner_text()

                # 🎯 entry-level filter
                if not any(x in text.lower() for x in ["intern", "junior", "0-1", "fresher", "associate"]):
                    continue

                results.append({
                    "Platform": "Wellfound",
                    "Company": text.split("\n")[0],
                    "Role": text,
                    "Link": page.url
                })

            except:
                continue