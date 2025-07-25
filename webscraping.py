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
    # for i, link in enumerate(links, 1):
    #     print(f"{i:02d}. {link['title']} — {link['url']}")
    # await browser.close()

async def scrape_details(context, program_info):

    details_page = await context.new_page()
    try:
        print(f"Scraping: {program_info['title']}")
        await details_page.goto(program_info['url'], timeout=60000)
        fee_text = await details_page.locator('dt:has-text("ค่าใช้จ่าย") + dd').inner_text()
        # print(f"  └── Tuition Fee: {fee.strip()}\n")

        processed_fee = fee_text

        per_semester_pattern = r'(\d{1,3}(?:,\d{3})*).*?(?:/|ต่อ)ภาคการศึกษา'
        per_program_pattern = r'(\d{1,3}(?:,\d{3})*).*?ตลอดหลักสูตร'

        semester_match = re.search(per_semester_pattern, fee_text)
        if semester_match:
            fee_str = semester_match.group(1).replace(',', '')
            fee_amount = int(fee_str)
            processed_fee = f"{fee_amount:,.0f} per semester"

        else:
            program_match = re.search(per_program_pattern, fee_text)
            if program_match:
                total_fee_str = program_match.group(1).replace(',', '')
                total_fee = int(total_fee_str)
                
                # Calculate semester fee by dividing by 8
                estimated_semester_fee = total_fee / 8
                processed_fee = f"{total_fee:,.0f} per program (Est. {estimated_semester_fee:,.0f} per semester)"

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
    asyncio.run(main(query="วิศวกรรมปัญญาประดิษฐ์"))
