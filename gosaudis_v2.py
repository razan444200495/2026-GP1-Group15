import json
import logging
import pandas as pd
from playwright.sync_api import sync_playwright

BASE_URL = "https://gosaudis.com/city/riyadh"

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
log = logging.getLogger(__name__)

def scrape_events():
    events = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # 1️⃣ افتح صفحة الرياض
        page.goto(BASE_URL)
        page.wait_for_timeout(5000)

        # Scroll
        for _ in range(6):
            page.mouse.wheel(0, 2000)
            page.wait_for_timeout(1500)

        # 2️⃣ جمع روابط الفعاليات
        event_links = page.locator("a[href^='/event/']")
        count = event_links.count()
        log.info(f"عدد الفعاليات: {count}")

        urls = []
        for i in range(count):
            href = event_links.nth(i).get_attribute("href")
            if href:
                full = f"https://gosaudis.com{href}"
                if full not in urls:
                    urls.append(full)

        # 3️⃣ ندخل كل فعالية
        for url in urls:
            try:
                page.goto(url)
                page.wait_for_timeout(4000)

                title = page.locator("h1").first.inner_text() if page.locator("h1").count() else ""

                category = ""
                cat = page.locator("[data-testid*='category']")
                if cat.count():
                    category = cat.first.inner_text()

                date = ""
                date_el = page.locator("[data-testid*='date']")
                if date_el.count():
                    date = date_el.first.inner_text()

                location = ""
                loc = page.locator("[data-testid*='location']")
                if loc.count():
                    location = loc.first.inner_text()

                description = ""
                desc = page.locator("p")
                if desc.count():
                    description = desc.first.inner_text()

                image = ""
                img = page.locator("img")
                if img.count():
                    image = img.first.get_attribute("src")

                price = ""
                price_el = page.locator("[data-testid*='price']")
                if price_el.count():
                    price = price_el.first.inner_text()

                # 🔥 أهم شيء: external link
                external_link = ""
                ext = page.locator("a[href^='http']").all()

                for e in ext:
                    href = e.get_attribute("href")
                    if href and "gosaudis.com" not in href:
                        external_link = href
                        break

                event_data = {
                    "title": title,
                    "category": category,
                    "city": "Riyadh",
                    "date": date,
                    "time": "",
                    "description": description,
                    "image": image,
                    "official_link": url,
                    "source": "GoSaudis",
                    "price": price,
                    "location": location,
                    "end_date": "",
                    "external_link": external_link
                }

                events.append(event_data)
                log.info(f"✅ {title}")

            except Exception as e:
                log.warning(f"خطأ في {url}: {e}")

        browser.close()

    return events


if __name__ == "__main__":
    data = scrape_events()

    with open("events.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    pd.DataFrame(data).to_excel("events.xlsx", index=False)

    print("✅ تم الانتهاء")