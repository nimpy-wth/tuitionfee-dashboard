import asyncio
from playwright.async_api import async_playwright

async def scrape_program_links(query="วิศวกรรมคอมพิวเตอร์"):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) 
        page = await browser.new_page()
        await page.goto("https://course.mytcas.com", timeout=60000)

        await page.wait_for_selector('input#search')
        await page.fill('input#search', '')
        await page.type('input#search', query, delay=100)
        await page.keyboard.press('Enter')
        await page.wait_for_selector('.t-programs li a', timeout=15000) 

        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_program_links())