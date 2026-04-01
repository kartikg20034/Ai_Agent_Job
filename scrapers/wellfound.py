def scrape_wellfound(page, keywords, results):
    page.goto("https://wellfound.com/jobs")
    page.wait_for_timeout(5000)

    jobs = page.query_selector_all("div")

    for job in jobs[:20]:
        try:
            results.append({
                "Platform": "Wellfound",
                "Company": "Startup",
                "Role": job.inner_text()[:80],
                "Link": page.url
            })
        except:
            continue