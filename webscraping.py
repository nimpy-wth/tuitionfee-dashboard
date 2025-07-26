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
        
        tuition = None
        if fee_text and fee_text != "_":
            
            def clean_fee(num_str):
                return int(re.sub(r'[^\d]', '', num_str.split('.')[0]))

            # find "per semester" fees
            semester_patterns = [
                r'([\d,.]+)\s*(?:บาท)?\s*ต่อ(?:ภาคเรียน|ภาคการศึกษา|เทอม)',
                r'(?:ภาคเรียน|ภาคการศึกษา|เทอม)ละ\s*([\d,.]+)',           
                r'เทอมแรก\s*([\d,.]+)',                                
                r'\(?([\d,.]+)\s*บาทในภาคการศึกษาแรก\)?',                 
                r'\(?([\d,.]+)\s*ต่อภาคเรียน\)?'                       
            ]
            for pattern in semester_patterns:
                match = re.search(pattern, fee_text)
                if match:
                    tuition = clean_fee(match.group(1))
                    break
            
            if tuition is None:
                # find "per program" fees and estimate
                program_pattern = r'ตลอดหลักสูตร\s*([\d,.]+)'
                match = re.search(program_pattern, fee_text)
                if match:
                    total_fee = clean_fee(match.group(1))
                    tuition = round(total_fee / 8)
                
            if tuition is None:
                # no keywords found
                number_match = re.search(r'(\d[\d,.]*)', fee_text)
                if number_match:
                    fee_amount = clean_fee(number_match.group(1))
                    if fee_amount > 50000 and "ภาษาไทย ปกติ" in (data["program_type"] or ""):
                        tuition = round(fee_amount / 8)
                    else:
                        tuition = fee_amount

        data["tuition_per_semester"] = tuition

        print(f"Scraping: {data['program_name']}")
        print(f" ├── University : {data['university']}")
        print(f" ├── Program Type: {data['program_type']}")
        print(f" └── Tuition Fee (per semester): {data['tuition_per_semester']}\n")

        return data

    except Exception as e:
        print(f" └── Could not find information for this program. Error: {e}\n")
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
    search_queries = [
        "วิศวกรรมคอมพิวเตอร์",
        "วิศวกรรมปัญญาประดิษฐ์",
        "วิศวกรรมหุ่นยนต์",
        "วิศวกรรมซอฟต์แวร์"
    ]
    
    asyncio.run(main(queries=search_queries))
