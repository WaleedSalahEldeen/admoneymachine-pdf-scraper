async def download_pdf(client, url, dest_path, semaphore):
    async with semaphore:
        try:
            await client.download_file(url, dest_path)
            return {"downloaded": True, "error": ""}
        except Exception as exc:
            return {"downloaded": False, "error": str(exc)}
