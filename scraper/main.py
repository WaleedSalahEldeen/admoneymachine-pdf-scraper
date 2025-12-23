import asyncio
from pathlib import Path

from scraper import config
from scraper.filesystem import ensure_dir
from scraper.http_client import HttpClient
from scraper.post_processor import process_post
from scraper.wp_api import fetch_all_categories, fetch_all_posts


async def run():
    output_dir = Path(config.OUTPUT_DIR)
    ensure_dir(output_dir)

    async with HttpClient(
        timeout=config.REQUEST_TIMEOUT,
        retries=config.MAX_RETRIES,
        backoff=config.RETRY_BACKOFF,
        max_connections=config.CONCURRENT_REQUESTS,
        user_agent=config.USER_AGENT,
    ) as client:
        print("Fetching categories...")
        categories = await fetch_all_categories(client)
        category_map = {item.get("id"): item.get("name") for item in categories}
        print("Categories: " + str(len(categories)))

        print("Fetching posts...")
        posts = await fetch_all_posts(client)
        print("Posts: " + str(len(posts)))

        post_semaphore = asyncio.Semaphore(config.CONCURRENT_POSTS)
        download_semaphore = asyncio.Semaphore(config.CONCURRENT_DOWNLOADS)
        tasks = []
        for post in posts:
            tasks.append(
                asyncio.create_task(
                    process_post_limited(
                        post,
                        category_map,
                        client,
                        output_dir,
                        post_semaphore,
                        download_semaphore,
                    )
                )
            )
        results = await asyncio.gather(*tasks)
        processed = len([item for item in results if item is not None])
        print("Finished posts: " + str(processed))


async def process_post_limited(
    post,
    category_map,
    client,
    output_dir,
    post_semaphore,
    download_semaphore,
):
    async with post_semaphore:
        post_id = post.get("id")
        try:
            return await process_post(
                post,
                category_map,
                client,
                output_dir,
                download_semaphore,
            )
        except Exception as exc:
            print("Post failed: " + str(post_id) + " error: " + str(exc))
            return None
