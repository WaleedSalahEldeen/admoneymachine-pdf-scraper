import asyncio
from html import unescape

from scraper import config


async def fetch_all_categories(client):
    items = await fetch_paginated(client, config.CATEGORIES_ENDPOINT, config.PER_PAGE)
    categories = []
    for item in items:
        name = unescape(item.get("name", "")).strip()
        categories.append({"id": item.get("id"), "name": name})
    return categories


async def fetch_all_posts(client):
    return await fetch_paginated(client, config.POSTS_ENDPOINT, config.PER_PAGE)


async def fetch_paginated(client, url, per_page):
    params = {"per_page": per_page, "page": 1}
    data, headers = await client.fetch_json(url, params=params)
    items = list(data or [])

    total_pages = headers.get("X-WP-TotalPages")
    if total_pages:
        total_pages = int(total_pages)
    if total_pages and total_pages > 1:
        tasks = []
        for page in range(2, total_pages + 1):
            tasks.append(asyncio.create_task(fetch_page(client, url, per_page, page)))
        pages = await asyncio.gather(*tasks)
        for page_items in pages:
            items.extend(page_items)
        return items

    page = 2
    while data:
        data, _ = await client.fetch_json(url, params={"per_page": per_page, "page": page})
        if not data:
            break
        items.extend(data)
        page += 1
    return items


async def fetch_page(client, url, per_page, page):
    data, _ = await client.fetch_json(url, params={"per_page": per_page, "page": page})
    return data or []
