from playwright.sync_api import sync_playwright
import json

base_url = "https://app.marketplace.autura.com"

def scrape_data(auctionid, city):
    data = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        page = browser.new_page()
        block_types = {"image", "media", "font",}
        page.route("**/*", lambda r: r.abort() if r.request.resource_type in block_types else r.continue_())

        url = f"{base_url}/auction/{city}/auction-{auctionid}"
        page.goto(url, wait_until="domcontentloaded")

        page.wait_for_selector('a[href*="/vehicle/"]')
        car_links = page.query_selector_all('a[href*="/vehicle/"]')

        vehicle_page = browser.new_page()
        vehicle_page.route("**/*", lambda r: r.abort() if r.request.resource_type in block_types else r.continue_())

        for link in car_links:
            href = link.get_attribute("href")
            vehicle_page.goto(f"{base_url}{href}", wait_until="domcontentloaded")

            table_block = vehicle_page.wait_for_selector("div.ant-table-content")
            rows = table_block.query_selector_all("tr")

            vehicle_data = {}
            for row in rows:
                cells = row.query_selector_all("td")
                name = cells[0].inner_text().strip()
                value = cells[1].inner_text().strip()
                vehicle_data[name] = value
            
            data.append(vehicle_data)

        # Close pages and browser after loop;../
        vehicle_page.close()
        page.close()
        browser.close()
    
    return data

def mileage_checker(Vin):
    pass

vehicles = scrape_data(108860, "SA-TX")
vehicles_json = json.dumps(vehicles, indent=2)
print(vehicles_json)
