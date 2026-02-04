import asyncio
import re
import json
from playwright.async_api import async_playwright

async def scrape_inspections():
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://www.mytxcar.org/TXCar_Net/VehicleTestDetail.aspx") 

        link_selector = "a[onclick*='DoSelect']"
        await page.wait_for_selector(link_selector)

        # 1. Grab all End Dates from the table first so we don't have to find them inside the loop
        # Column 0 is Begin Date (the link), Column 1 is End Date Time
        rows = page.locator("table tbody tr").filter(has=page.locator(link_selector))
        count = await rows.count()
        
        # Store dates in a list to pair them up later
        end_dates = []
        for i in range(count):
            date_text = await rows.nth(i).locator("td").nth(1).inner_text()
            end_dates.append(date_text.strip())

        # 2. Now loop through and click the links
        for i in range(count):
            # Re-locate the link list because of the page refresh
            links = page.locator(link_selector)
            current_link = links.nth(i)

            # Get the ID from onclick for the record
            onclick_text = await current_link.get_attribute("onclick")
            row_id_match = re.search(r"DoSelect\('[^']+', '[^']+', '(\d+)'", onclick_text)
            row_id = row_id_match.group(1) if row_id_match else f"Unknown_{i}"

            # Navigate to detail page
            await current_link.click()

            try:
                # Wait for detail data
                await page.wait_for_selector("td:has-text('Odometer')", timeout=5000)
                odometer_text = await page.text_content("td:has-text('Odometer') + td")
                
                results.append({
                    "row_id": row_id,
                    "date": end_dates[i], # Pair with the date we grabbed earlier
                    "odometer": odometer_text.strip() if odometer_text else "N/A"
                })

            except Exception:
                pass 

            # Go Back
            await page.click("#btnBack")
            await page.wait_for_selector(link_selector)
            await page.wait_for_timeout(100)

        await browser.close()
        return results

if __name__ == "__main__":
    data = asyncio.run(scrape_inspections())
    print(json.dumps(data, indent=2))