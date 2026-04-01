def scrape_linkedin(page, keywords, locations, results, parse_posted_time):
    print("🔍 LinkedIn scanning...")

    for keyword in keywords:
        for loc in locations:
            page.goto(f"https://www.linkedin.com/jobs/search/?keywords={keyword}&location={loc}")
            page.wait_for_timeout(4000)

            jobs = page.query_selector_all(".job-card-container")

            for job in jobs[:6]:
                try:
                    job.click()
                    page.wait_for_timeout(2000)

                    title = page.query_selector("h2").inner_text()
                    company = page.query_selector(".job-details-jobs-unified-top-card__company-name").inner_text()
                    link = page.url

                    posted = page.query_selector("span.tvm__text")
                    posted_text = posted.inner_text() if posted else "unknown"
                    days = parse_posted_time(posted_text)

                    if days <= 3:
                        results.append({
                            "Platform": "LinkedIn",
                            "Company": company,
                            "Role": title,
                            "Posted": posted_text,
                            "Days_Ago": days,
                            "Link": link
                        })

                except:
                    continue