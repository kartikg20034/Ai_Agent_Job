def scrape_linkedin(page, keywords, locations, results):
    print("🔵 LinkedIn...")

    for keyword in keywords:
        for loc in locations:
            url = f"https://www.linkedin.com/jobs/search/?keywords={keyword}&location={loc}&f_E=2"
            page.goto(url)
            page.wait_for_timeout(5000)

            # scroll to load more jobs
            for _ in range(3):
                page.mouse.wheel(0, 4000)
                page.wait_for_timeout(2000)

            jobs = page.query_selector_all(".jobs-search-results__list-item")

            for job in jobs[:25]:
                try:
                    title = job.query_selector("h3").inner_text()
                    company = job.query_selector("h4").inner_text()
                    link = job.query_selector("a").get_attribute("href")

                    # 🎯 filter entry-level
                    if not any(x in title.lower() for x in ["intern", "junior", "associate", "engineer i", "sde 1"]):
                        continue

                    results.append({
                        "Platform": "LinkedIn",
                        "Company": company,
                        "Role": title,
                        "Link": link
                    })

                except:
                    continue