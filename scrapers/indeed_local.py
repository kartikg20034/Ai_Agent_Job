def scrape_indeed_local(page, keywords, locations, results):
    print("🌐 Indeed (Local)...")

    for keyword in keywords:
        for loc in locations:
            url = f"https://in.indeed.com/jobs?q={keyword}&l={loc}"
            page.goto(url)
            page.wait_for_timeout(4000)

            jobs = page.query_selector_all(".job_seen_beacon")

            for job in jobs[:20]:
                try:
                    title = job.query_selector("h2").inner_text()
                    company = job.query_selector(".companyName").inner_text()
                    link = job.query_selector("a").get_attribute("href")

                    results.append({
                        "Platform": "Indeed",
                        "Company": company,
                        "Role": title + " fresher intern",
                        "Link": "https://in.indeed.com" + link
                    })
                except:
                    continue