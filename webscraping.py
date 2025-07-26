import asyncio
from playwright.async_api import async_playwright
import re
import json

async def search_for_programs(page, query):
    
    await page.goto("https://course.mytcas.com", timeout=60000)

    # search for the query
    await page.wait_for_selector('input#search')
    await page.fill('input#search', '')
    await page.type('input#search', query, delay=100)
    await page.keyboard.press('Enter')
    await page.wait_for_selector('.t-programs li a', timeout=15000) 

    # extract results
    links = await page.eval_on_selector_all(
        ".t-programs li a",
        "els => els.map(el => ({ title: el.innerText.trim(), url: el.href }))"
        )
        
    print(f"Found {len(links)} results for: {query}")
    return links

async def scrape_details(context, program_info):

    details_page = await context.new_page()
    title_parts = program_info['title'].split('\n')
    university_campus = title_parts[-1] if len(title_parts) > 1 else "N/A"

    data = {
        "program_name": title_parts[0],
        "university": university_campus,
        "url": program_info['url'],
        "degree_name_en": None,
        "program_type": None,
        "tuition_per_semester": None,
        "raw_fee_text": None,
    }

    try:
        await details_page.goto(program_info['url'], timeout=60000)

        # helper function for dt + dd text
        async def get_text_by_dt(label):
            try:
                locator = details_page.locator(f'dt:has-text("{label}") + dd')
                await locator.wait_for(timeout=1500)
                return await locator.inner_text()
            except Exception:
                return None

        data["degree_name_en"] = await get_text_by_dt("ชื่อหลักสูตรภาษาอังกฤษ")
        data["program_type"] = await get_text_by_dt("ประเภทหลักสูตร")
        fee_text = await get_text_by_dt("ค่าใช้จ่าย")
        data["raw_fee_text"] = fee_text

        processed_fee = "Not available"
        if fee_text and fee_text != "_":
            semester_keywords = ["ภาคการศึกษา", "ภาคเรียน", "เทอม"]
            program_keywords = ["ตลอดหลักสูตร"]

            number_pattern = r'(\d[\d,.]*)'
            number_match = re.search(number_pattern, fee_text)

            # check for "per semester" keywords
            if any(keyword in fee_text for keyword in semester_keywords):
                if number_match:
                    fee_amount = int(number_match.group(1).replace(',', '').split('.')[0])
                    data["tuition_per_semester"] = fee_amount
                    processed_fee = f"{fee_amount:,.0f} per semester"

            # check for "per program" keywords
            elif any(keyword in fee_text for keyword in program_keywords):
                if number_match:
                    total_fee = int(number_match.group(1).replace(',', '').split('.')[0])
                    est_semester_fee = round(total_fee / 8)
                    data["tuition_per_semester"] = est_semester_fee
                    processed_fee = f"{total_fee:,.0f} per program (Est. {est_semester_fee:,.0f} per semester)"

            # no keywords found
            elif number_match and "http" not in fee_text:
                fee_amount = int(number_match.group(1).replace(',', '').split('.')[0])
                if "ภาษาไทย ปกติ" in (data["program_type"] or ""):
                    est_fee = round(fee_amount / 8)
                    data["tuition_per_semester"] = est_fee
                    processed_fee = f"{fee_amount:,.0f} per program (Est. {est_fee:,.0f} per semester)"
                else:
                    processed_fee = f"{fee_amount:,.0f} (description unclear)"
                    data["tuition_per_semester"] = fee_amount
        
        print(f"Scraping: {data['program_name']}")
        print(f"  ├── University : {data['university']}")
        print(f"  ├── Program Type: {data['program_type']}")
        print(f"  └── Tuition Fee (per semester): {data['tuition_per_semester']}\n")

        return data

    except Exception as e:
        print(f"  └── Could not find information for this program. Error: {e}\n")
        return None
    finally:
        await details_page.close()

async def main(queries):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        scraped_program_map = {}

        print(f"Starting to scrape for {len(queries)} queries...")

        for query in queries:
            print(f"\nSearching for: '{query}'...")
            program_links = await search_for_programs(page, query)

            print(f"--- Processing results for query: '{query}' ---")
            for link in program_links:
                url = link['url']
                program_name = link['title'].split('\n')[0]

                # check if this program is already in collection
                if url in scraped_program_map:
                    scraped_program_map[url]['keywords'].append(query)
                    print(f"  └── Found duplicate: '{program_name}'. Appending keyword '{query}'.")
                else:
                    scraped_data = await scrape_details(context, link)
                    if scraped_data:
                        scraped_data['keywords'] = [query]
                        scraped_program_map[url] = scraped_data

        # convert dictionary to list for JSON
        all_programs_data = list(scraped_program_map.values())

        # save the collected data
        output_filename = "tcas_data.json"
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(all_programs_data, f, ensure_ascii=False, indent=4)

        print(f" Scraping Complete! ")
        print(f"\nData saved to {output_filename}")
        
        await context.close()
        await browser.close()

if __name__ == "__main__":
    # asyncio.run(main(query="วิศวกรรมปัญญาประดิษฐ์"))
    search_queries = [
        "วิศวกรรมคอมพิวเตอร์",
        "วิศวกรรมปัญญาประดิษฐ์",    
        "วิศวกรรมหุ่นยนต์",
        "วิศวกรรม ปัญญาประดิษฐ์",
        "วิศวกรรมซอฟต์แวร์"
    ]
    
    asyncio.run(main(queries=search_queries))
