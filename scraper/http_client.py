import asyncio
import os
import random

import aiofiles
import aiohttp


class HttpStatusError(Exception):
    def __init__(self, status, url):
        super().__init__("http status " + str(status) + " for " + url)
        self.status = status
        self.url = url


class HttpClient:
    def __init__(self, timeout, retries, backoff, max_connections, user_agent):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.retries = retries
        self.backoff = backoff
        self.connector = aiohttp.TCPConnector(limit=max_connections)
        self.headers = {"User-Agent": user_agent}
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=self.timeout,
            headers=self.headers,
            connector=self.connector,
        )
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        if self.session:
            await self.session.close()

    async def fetch_json(self, url, params=None):
        return await self._request_json("GET", url, params)

    async def _request_json(self, method, url, params=None):
        last_error = None
        for attempt in range(self.retries):
            try:
                async with self.session.request(method, url, params=params) as response:
                    if response.status in (429, 500, 502, 503, 504):
                        raise HttpStatusError(response.status, url)
                    if response.status >= 400:
                        raise HttpStatusError(response.status, url)
                    data = await response.json()
                    return data, response.headers
            except (aiohttp.ClientError, asyncio.TimeoutError, HttpStatusError) as exc:
                last_error = exc
                if attempt >= self.retries - 1:
                    break
                await asyncio.sleep(self._backoff_delay(attempt))
        raise last_error

    async def download_file(self, url, dest_path, chunk_size=65536):
        last_error = None
        for attempt in range(self.retries):
            try:
                async with self.session.get(url) as response:
                    if response.status in (429, 500, 502, 503, 504):
                        raise HttpStatusError(response.status, url)
                    if response.status >= 400:
                        raise HttpStatusError(response.status, url)
                    async with aiofiles.open(dest_path, "wb") as handle:
                        async for chunk in response.content.iter_chunked(chunk_size):
                            await handle.write(chunk)
                return
            except (aiohttp.ClientError, asyncio.TimeoutError, HttpStatusError) as exc:
                last_error = exc
                if os.path.exists(dest_path):
                    try:
                        os.remove(dest_path)
                    except OSError:
                        pass
                if attempt >= self.retries - 1:
                    break
                await asyncio.sleep(self._backoff_delay(attempt))
        raise last_error

    def _backoff_delay(self, attempt):
        return (self.backoff * (2 ** attempt)) + random.uniform(0, 0.5)
