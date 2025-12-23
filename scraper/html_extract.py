from html import unescape
from html.parser import HTMLParser
from urllib.parse import urljoin


class PdfLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self._current_href = None
        self._current_text = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        href = None
        for key, value in attrs:
            if key.lower() == "href":
                href = value
                break
        self._current_href = href
        self._current_text = []

    def handle_data(self, data):
        if self._current_href is not None:
            self._current_text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() != "a":
            return
        if self._current_href is None:
            return
        text = "".join(self._current_text)
        self.links.append((self._current_href, text))
        self._current_href = None
        self._current_text = []


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def get_text(self):
        return "".join(self.parts)


def strip_html(html_text):
    if not html_text:
        return ""
    parser = TextExtractor()
    parser.feed(html_text)
    return parser.get_text()


def extract_pdf_links(html_text, base_url):
    parser = PdfLinkParser()
    parser.feed(html_text or "")
    results = []
    seen = set()
    for href, text in parser.links:
        if not href:
            continue
        url = urljoin(base_url, href)
        if ".pdf" not in url.lower():
            continue
        clean_text = unescape(text or "").strip()
        clean_text = " ".join(clean_text.split())
        if url in seen:
            continue
        seen.add(url)
        results.append({"url": url, "text": clean_text})
    return results
