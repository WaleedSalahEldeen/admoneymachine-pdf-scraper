from html import unescape
from pathlib import Path
from urllib.parse import urlparse

from scraper import config
from scraper.downloader import download_pdf
from scraper.filesystem import ensure_dir, safe_filename, write_json
from scraper.html_extract import extract_pdf_links, strip_html


def make_post_dir(output_dir, title, post_id):
    base_name = safe_filename(title, default="post-" + str(post_id))
    post_dir = Path(output_dir) / base_name
    if post_dir.exists():
        post_dir = Path(output_dir) / safe_filename(base_name + "-" + str(post_id))
    ensure_dir(post_dir)
    return post_dir


def build_pdf_filename(link_text, url, used_names):
    name_source = link_text
    if not name_source:
        name_source = Path(urlparse(url).path).name or "document"
    base_name = safe_filename(name_source, default="document")
    if not base_name.lower().endswith(".pdf"):
        base_name = base_name + ".pdf"
    candidate = base_name
    counter = 2
    while candidate in used_names:
        if base_name.lower().endswith(".pdf"):
            stem = base_name[:-4]
            candidate = stem + "-" + str(counter) + ".pdf"
        else:
            candidate = base_name + "-" + str(counter)
        counter += 1
    used_names.add(candidate)
    return candidate


async def process_post(post, category_map, client, output_dir, download_semaphore):
    post_id = post.get("id")
    title_html = post.get("title", {}).get("rendered", "")
    title_text = unescape(strip_html(title_html)).strip()
    content_html = post.get("content", {}).get("rendered", "")
    date_value = post.get("date", "")

    category_ids = post.get("categories") or []
    category_names = [category_map.get(cat_id, "") for cat_id in category_ids]

    pdf_links = extract_pdf_links(content_html, config.BASE_URL)
    post_dir = make_post_dir(output_dir, title_text, post_id)

    used_names = set()
    pdfs = []
    for link in pdf_links:
        link_text = link.get("text", "")
        file_name = build_pdf_filename(link_text, link.get("url"), used_names)
        dest_path = Path(post_dir) / file_name
        result = await download_pdf(client, link.get("url"), str(dest_path), download_semaphore)
        pdfs.append(
            {
                "url": link.get("url"),
                "link_text": link_text,
                "file_name": file_name,
                "downloaded": result.get("downloaded"),
                "error": result.get("error"),
            }
        )

    metadata = {
        "post_id": post_id,
        "post_title": title_text,
        "date": date_value,
        "category_ids": category_ids,
        "category_names": category_names,
        "pdfs": pdfs,
    }
    write_json(Path(post_dir) / "metadata.json", metadata)
    return metadata
