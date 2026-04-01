def scrape_indeed(page, keywords, locations, results, parse_posted_time):
    for keyword in keywords:
        for loc in locations:
            page.goto(f"https://in.indeed.com/jobs?q={keyword}&l={loc}")
            page.wait_for_timeout(3000)

            jobs = page.query_selector_all(".job_seen_beacon")

            for job in jobs[:5]:
                try:
                    title = job.query_selector("h2").inner_text()
                    company = job.query_selector(".companyName").inner_text()
                    link = job.query_selector("a").get_attribute("href")

                    results.append({
                        "Platform": "Indeed",
                        "Company": company,
                        "Role": title,
                        "Link": "https://in.indeed.com" + link
                    })
                except:
                    continue