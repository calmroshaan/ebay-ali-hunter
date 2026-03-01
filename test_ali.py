# test_ali.py
import asyncio
from scrapers.browser import BrowserManager
from scrapers.ali_scraper import scrape_aliexpress


async def test():
    manager = BrowserManager()
    await manager.start()

    context = await manager.new_context("aliexpress")

    print("\n--- Starting AliExpress test ---\n")
    results = await scrape_aliexpress(context, "wireless earbuds")

    print(f"\n--- Found {len(results)} results ---\n")
    for i, product in enumerate(results[:5]):
        print(f"Product {i+1}:")
        print(f"  Title    : {product['ali_title']}")
        print(f"  Price    : ${product['ali_price']}")
        print(f"  Shipping : ${product['ali_shipping']}")
        print()

    await manager.save_state(context, "aliexpress")
    await context.close()
    await manager.close()


asyncio.run(test())