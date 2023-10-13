"""Extracting and checking links."""

import concurrent.futures
import logging
from typing import Iterable

import markdown_it
import requests


logger = logging.getLogger(__name__)


def find_links(markdown_text: str) -> Iterable[str]:
    def walk_tokens(tokens):
        for token in tokens:
            if token.type == "link_open":
                yield token.attrs["href"]
            if token.children:
                yield from walk_tokens(token.children)

    yield from walk_tokens(markdown_it.MarkdownIt().parse(markdown_text))


def check_markdown_links(markdown_text: str) -> None:
    links = set(find_links(markdown_text))
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Start the load operations and mark each future with its URL
        futures = [executor.submit(check_one_link, url) for url in links]
        concurrent.futures.wait(futures)


def check_one_link(url):
    while True:
        try:
            resp = requests.head(url, timeout=60, allow_redirects=True)
        except requests.RequestException as exc:
            logger.warning(f"Failed check for {url!r}: {exc}")
            return
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", 10))
            time.sleep(wait + 1)
        else:
            break

    if resp.status_code == 200:
        logger.debug(f"OK link: {url!r}")
    else:
        logger.warning(f"Failed check for {url!r}: status code {resp.status_code}")
