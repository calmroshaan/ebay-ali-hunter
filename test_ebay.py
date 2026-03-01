# test_ebay.py
import asyncio
from scrapers.browser import BrowserManager
from scrapers.ebay_scraper import scrape_ebay


async def test():
    manager = BrowserManager()
    await manager.start()

    context = await manager.new_context("ebay")

    print("\n--- Starting eBay test ---\n")
    results = await scrape_ebay(context, "wireless earbuds")

    print(f"\n--- Found {len(results)} results ---\n")
    for i, product in enumerate(results[:5]):
        print(f"Product {i+1}:")
        print(f"  Title    : {product['title']}")
        print(f"  Price    : ${product['ebay_price']}")
        print(f"  Shipping : ${product['ebay_shipping']}")
        print(f"  Sold     : {product['sold_count']}")
        print(f"  Rating   : {product['seller_rating']}")
        print()

    await manager.save_state(context, "ebay")
    await context.close()
    await manager.close()


asyncio.run(test())