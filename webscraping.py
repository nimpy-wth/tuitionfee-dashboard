import asyncio
from playwright.async_api import async_playwright

async def search_for_programs(query="วิศวกรรมปัญญาประดิษฐ์"):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) 
        page = await browser.new_page()
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
    await details_page.goto(program_info['url'], timeout=60000)

    fee = await details_page.locator('dt:has-text("ค่าใช้จ่าย") + dd').inner_text()
    print(f"  └── Tuition Fee: {fee.strip()}\n")

    await details_page.close()

if __name__ == "__main__":
    asyncio.run(search_for_programs())
