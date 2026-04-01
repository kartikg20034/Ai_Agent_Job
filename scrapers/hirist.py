def scrape_hirist(page, results):
    page.goto("https://www.hirist.com/jobs")
    page.wait_for_timeout(4000)

    jobs = page.query_selector_all("li")

    for job in jobs[:20]:
        try:
            results.append({
                "Platform": "Hirist",
                "Company": "Various",
                "Role": job.inner_text()[:80],
                "Link": page.url
            })
        except:
            continue