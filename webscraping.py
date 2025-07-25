import asyncio
from playwright.async_api import async_playwright
import re

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
    try:
        print(f"Scraping: {program_info['title']}")
        await details_page.goto(program_info['url'], timeout=60000)
        fee_text = await details_page.locator('dt:has-text("ค่าใช้จ่าย") + dd').inner_text()

        processed_fee = fee_text

        if not fee_text or fee_text == "_":
            processed_fee = "Not available"
        
        else:
            semester_keywords = ["ภาคการศึกษา", "ภาคเรียน", "เทอม"]
            program_keywords = ["ตลอดหลักสูตร"]

            number_pattern = r'(\d[\d,.]*)'
            number_match = re.search(number_pattern, fee_text)

            # check for "per semester" keywords
            if any(keyword in fee_text for keyword in semester_keywords):
                if number_match:
                    fee_str = number_match.group(1).replace(',', '').split('.')[0]
                    fee_amount = int(fee_str)
                    processed_fee = f"{fee_amount:,.0f} per semester"

            # check for "per program" keywords
            elif any(keyword in fee_text for keyword in program_keywords):
                if number_match:
                    total_fee_str = number_match.group(1).replace(',', '').split('.')[0]
                    total_fee = int(total_fee_str)
                    estimated_semester_fee = total_fee / 8
                    processed_fee = f"{total_fee:,.0f} per program (Est. {estimated_semester_fee:,.0f} per semester)"

            # no keywords found
            elif number_match and "http" not in fee_text:
                fee_str = number_match.group(1).replace(',', '').split('.')[0]
                fee_amount = int(fee_str)                    
                processed_fee = f"{fee_amount:,.0f} (description unclear)"

        print(f"  └── Tuition Fee: {processed_fee}\n")

    except Exception as e:
        print(f"  └── Could not find information for this program.\n")
    finally:
        await details_page.close()

async def main(query):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # get all program links
        program_links = await search_for_programs(page, query)
        await page.close() 

        # scrape each program's details
        for link in program_links:
            await scrape_details(context, link)

        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main(query="วิศวกรรม ปัญญาประดิษฐ์"))
