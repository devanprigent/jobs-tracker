from __future__ import annotations

import html
import re
import urllib.parse
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import TypedDict


class UserPayload(TypedDict):
    id: int
    email: str


@dataclass(frozen=True)
class Site:
    company: str
    provider: str
    url: str


@dataclass(frozen=True)
class Job:
    company: str
    title: str
    location: str
    department: str
    url: str
    source: str
    date_found: str


class LinkExtractor(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self._current_href: str | None = None
        self._current_text: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attrs_dict = {name.lower(): value for name, value in attrs}
        href = attrs_dict.get("href")
        if href:
            self._current_href = urllib.parse.urljoin(self.base_url, href)
            self._current_text = []

    def handle_data(self, data: str) -> None:
        if self._current_href is not None:
            self._current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or self._current_href is None:
            return
        text = clean_link_text(" ".join(self._current_text))
        self.links.append((text, self._current_href))
        self._current_href = None
        self._current_text = []


def clean_link_text(value: str) -> str:
    value = html.unescape(str(value or ""))
    return re.sub(r"\s+", " ", value).strip()
