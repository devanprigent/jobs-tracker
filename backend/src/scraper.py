#!/usr/bin/env python3
"""Collect job offers from a list of company careers pages.

The scraper prefers structured/public sources when they are available and falls
back to extracting plausible job links from the page HTML. It is intentionally
polite: one request at a time, a normal user agent, and no login automation.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .types import Job, LinkExtractor, Site


BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SITES_JSON = BACKEND_DIR / "sites.json"
DEFAULT_CSV_OUTPUT = BACKEND_DIR / "jobs.csv"
DEFAULT_JSON_OUTPUT = BACKEND_DIR / "jobs.json"
TIMEOUT_SECONDS = 30
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape job offers from company career sites listed in sites.json."
    )
    parser.add_argument(
        "--sites",
        default=str(DEFAULT_SITES_JSON),
        help="Path to a JSON file containing company, provider, and URL entries.",
    )
    parser.add_argument(
        "--csv",
        default=str(DEFAULT_CSV_OUTPUT),
        help="CSV output path.",
    )
    parser.add_argument(
        "--json",
        default=str(DEFAULT_JSON_OUTPUT),
        help="JSON output path.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay in seconds between site requests.",
    )
    return parser.parse_args()


def clean_text(value: Any) -> str:
    value = html.unescape(str(value or ""))
    return re.sub(r"\s+", " ", value).strip()


def read_sites(path: Path) -> list[Site]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain a JSON array of site objects.")

    sites: list[Site] = []
    required = {"company", "provider", "url"}
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"{path} entry #{index} must be an object.")
        missing = required - set(item)
        if missing:
            missing_columns = ", ".join(sorted(missing))
            raise ValueError(f"{path} entry #{index} is missing required field(s): {missing_columns}")

        url = clean_text(item.get("url"))
        if not url:
            continue
        company = clean_text(item.get("company")) or company_from_url(url)
        provider = normalize_provider(item.get("provider"))
        sites.append(Site(company=company, provider=provider, url=url))
    return sites


def normalize_provider(provider: str | None) -> str:
    provider = clean_text(provider).casefold().replace("_", "-")
    return provider or "auto"


def request_url(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/json",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def request_json(url: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def company_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    host_parts = parsed.netloc.lower().split(".")
    if "smartrecruiters" in parsed.netloc.lower():
        first_path_part = parsed.path.strip("/").split("/", 1)[0]
        return first_path_part or "SmartRecruiters"
    if parsed.netloc.lower() == "jobs.lever.co":
        first_path_part = parsed.path.strip("/").split("/", 1)[0]
        return format_company(first_path_part) or "Lever"
    if "freshteam" in parsed.netloc.lower():
        return format_company(host_parts[0])
    if len(host_parts) == 2 and host_parts[0] == "careers":
        return format_company(host_parts[1])
    if len(host_parts) >= 3 and ".".join(host_parts[-2:]) in {"co.uk", "com.au", "co.nz"}:
        return format_company(host_parts[-3])
    if len(host_parts) >= 2:
        return format_company(host_parts[-2])
    return parsed.netloc or "Unknown"


def format_company(value: str) -> str:
    name = value.replace("-", " ").title()
    return {"Cern": "CERN"}.get(name, name)


def scrape_site(site: Site, date_found: str) -> list[Job]:
    provider = site.provider
    parsed = urllib.parse.urlparse(site.url)
    if provider == "auto":
        provider = detect_provider(site.url)

    if provider == "smartrecruiters":
        return scrape_smartrecruiters(site, date_found)
    if provider == "lever":
        return scrape_lever(site, date_found)

    html_text = request_url(site.url)
    jobs = extract_json_ld_jobs(html_text, site.url, date_found, site.company)
    jobs.extend(extract_link_jobs(html_text, site.url, date_found, site.company))
    return dedupe_jobs(jobs)


def detect_provider(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower()
    if "smartrecruiters.com" in host:
        return "smartrecruiters"
    if host == "jobs.lever.co":
        return "lever"
    return "html"


def scrape_smartrecruiters(site: Site, date_found: str) -> list[Job]:
    parsed = urllib.parse.urlparse(site.url)
    company = parsed.path.strip("/").split("/", 1)[0]
    if not company:
        return []
    display_company = site.company or company

    jobs: list[Job] = []
    offset = 0
    limit = 100

    while True:
        api_url = (
            "https://api.smartrecruiters.com/v1/companies/"
            f"{urllib.parse.quote(company)}/postings?limit={limit}&offset={offset}"
        )
        data = request_json(api_url)
        postings = data.get("content") or []
        if not postings:
            break

        for posting in postings:
            title = clean_text(posting.get("name"))
            job_id = clean_text(posting.get("id"))
            location = posting.get("location") or {}
            location_text = clean_text(location.get("fullLocation") or location.get("city"))
            department = clean_text(posting.get("department", {}).get("label"))
            slug = slugify(title)
            job_url = f"https://jobs.smartrecruiters.com/{company}/{job_id}-{slug}"
            if title and job_url:
                jobs.append(
                    Job(
                        company=display_company,
                        title=title,
                        location=location_text,
                        department=department,
                        url=job_url,
                        source="smartrecruiters",
                        date_found=date_found,
                    )
                )

        offset += limit
        total = int(data.get("totalFound") or len(jobs))
        if offset >= total:
            break

    return dedupe_jobs(jobs)


def scrape_lever(site: Site, date_found: str) -> list[Job]:
    parsed = urllib.parse.urlparse(site.url)
    company = parsed.path.strip("/").split("/", 1)[0]
    if not company:
        return []
    display_company = site.company or format_company(company)

    api_url = f"https://api.lever.co/v0/postings/{urllib.parse.quote(company)}?mode=json"
    postings = request_json(api_url)
    if not isinstance(postings, list):
        return []

    jobs: list[Job] = []
    for posting in postings:
        categories = posting.get("categories") or {}
        title = clean_text(posting.get("text"))
        job_url = clean_text(posting.get("hostedUrl") or posting.get("applyUrl"))
        if not title or not job_url:
            continue
        jobs.append(
            Job(
                company=display_company,
                title=title,
                location=clean_text(categories.get("location")),
                department=clean_text(categories.get("team")),
                url=job_url,
                source="lever",
                date_found=date_found,
            )
        )
    return dedupe_jobs(jobs)


def extract_json_ld_jobs(
    html_text: str, page_url: str, date_found: str, company: str = ""
) -> list[Job]:
    jobs: list[Job] = []
    scripts = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    for script in scripts:
        try:
            payload = json.loads(html.unescape(script.strip()))
        except json.JSONDecodeError:
            continue
        for item in iter_json_items(payload):
            if item.get("@type") != "JobPosting":
                continue
            title = clean_text(item.get("title"))
            job_url = clean_text(item.get("url") or page_url)
            if not title:
                continue
            jobs.append(
                Job(
                    company=company or extract_json_company(item) or company_from_url(page_url),
                    title=title,
                    location=extract_json_location(item),
                    department=clean_text(item.get("employmentType")),
                    url=urllib.parse.urljoin(page_url, job_url),
                    source="json-ld",
                    date_found=date_found,
                )
            )
    return dedupe_jobs(jobs)


def iter_json_items(payload: Any) -> Iterable[dict[str, Any]]:
    if isinstance(payload, dict):
        graph = payload.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                yield from iter_json_items(item)
        else:
            yield payload
    elif isinstance(payload, list):
        for item in payload:
            yield from iter_json_items(item)


def extract_json_company(item: dict[str, Any]) -> str:
    organization = item.get("hiringOrganization")
    if isinstance(organization, dict):
        return clean_text(organization.get("name"))
    return clean_text(organization)


def extract_json_location(item: dict[str, Any]) -> str:
    location = item.get("jobLocation")
    if isinstance(location, list):
        return "; ".join(filter(None, (extract_place_location(place) for place in location)))
    if isinstance(location, dict):
        return extract_place_location(location)
    return clean_text(location)


def extract_place_location(place: dict[str, Any]) -> str:
    address = place.get("address")
    if not isinstance(address, dict):
        return clean_text(place.get("name"))
    parts = [
        address.get("addressLocality"),
        address.get("addressRegion"),
        address.get("addressCountry"),
    ]
    return clean_text(", ".join(str(part) for part in parts if part))


def extract_link_jobs(
    html_text: str, page_url: str, date_found: str, company: str = ""
) -> list[Job]:
    parser = LinkExtractor(page_url)
    parser.feed(html_text)

    company = company or company_from_url(page_url)
    jobs: list[Job] = []
    for text, href in parser.links:
        if not looks_like_job_link(text, href, page_url):
            continue
        title = infer_title(text, href)
        if not title:
            continue
        jobs.append(
            Job(
                company=company,
                title=title,
                location="",
                department="",
                url=href,
                source="html-link",
                date_found=date_found,
            )
        )
    return dedupe_jobs(jobs)


def looks_like_job_link(text: str, href: str, page_url: str) -> bool:
    parsed_href = urllib.parse.urlparse(href)
    parsed_page = urllib.parse.urlparse(page_url)
    normalized_href = parsed_href._replace(query="", fragment="").geturl().rstrip("/")
    normalized_page = parsed_page._replace(query="", fragment="").geturl().rstrip("/")
    if normalized_href == normalized_page:
        return False
    if parsed_href.fragment and not parsed_href.path.rstrip("/").lower().endswith(("/job", "/jobs")):
        return False
    if parsed_href.netloc and parsed_href.netloc != parsed_page.netloc:
        allowed_external = {"jobs.smartrecruiters.com", "boards.greenhouse.io", "jobs.lever.co"}
        if parsed_href.netloc.lower() not in allowed_external:
            return False

    lowered_text = text.lower()
    lowered_path = urllib.parse.unquote(parsed_href.path.lower())
    generic_labels = {
        "apply",
        "careers",
        "clear filters",
        "current job openings",
        "go to top",
        "here",
        "job openings",
        "jobs",
        "learn more",
        "manage cookies",
        "next jobs",
        "search jobs",
        "skip to main content",
        "view all jobs",
    }
    if lowered_text in generic_labels or "job alerts" in lowered_text:
        return False
    if len(text) > 140:
        return False
    if re.search(r"/(rjc-)?job/", lowered_path) or re.search(r"/jobs/[^/?#]+", lowered_path):
        return True
    if parsed_href.netloc.lower() == "jobs.lever.co":
        lever_path = parsed_href.path.strip("/").split("/")
        return len(lever_path) >= 2 and looks_like_uuid(lever_path[1])
    if parsed_href.netloc.lower() == "join.com":
        join_path = parsed_href.path.strip("/").split("/")
        return len(join_path) >= 3 and join_path[0] == "companies"
    return False


def infer_title(text: str, href: str) -> str:
    text = clean_text(text)
    if 4 <= len(text) <= 140 and text.lower() != "view job":
        return text

    path = urllib.parse.unquote(urllib.parse.urlparse(href).path)
    slug = path.rstrip("/").split("/")[-1]
    slug = re.sub(r"^\d+[-_]", "", slug)
    return clean_text(slug.replace("-", " ").replace("_", " ")).title()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "job"


def looks_like_uuid(value: str) -> bool:
    return bool(
        re.fullmatch(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            value.lower(),
        )
    )


def dedupe_jobs(jobs: Iterable[Job]) -> list[Job]:
    by_key: dict[tuple[str, str], Job] = {}
    for job in jobs:
        key = (job.company.casefold(), job.url.casefold())
        existing = by_key.get(key)
        if existing is None or job_quality(job) > job_quality(existing):
            by_key[key] = job
    return sorted(by_key.values(), key=lambda job: (job.company.casefold(), job.title.casefold()))


def job_quality(job: Job) -> int:
    generic_titles = {"view job", "job", "jobs"}
    score = len(job.title)
    if job.title.casefold() in generic_titles:
        score -= 100
    if job.location:
        score += 10
    if job.department:
        score += 5
    if job.source != "html-link":
        score += 20
    return score


def write_csv(path: Path, jobs: list[Job]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["company", "title", "location", "department", "url", "source", "date_found"],
        )
        writer.writeheader()
        for job in jobs:
            writer.writerow(asdict(job))


def write_json(path: Path, jobs: list[Job]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([asdict(job) for job in jobs], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    sites_file = Path(args.sites)
    csv_output = Path(args.csv)
    json_output = Path(args.json)
    date_found = datetime.now(timezone.utc).date().isoformat()

    all_jobs: list[Job] = []
    for site in read_sites(sites_file):
        print(f"Scraping {site.company} ({site.provider}): {site.url}")
        try:
            jobs = scrape_site(site, date_found)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            print(f"  failed: {exc}")
            continue
        print(f"  found {len(jobs)} jobs")
        all_jobs.extend(jobs)
        time.sleep(max(args.delay, 0))

    all_jobs = dedupe_jobs(all_jobs)
    write_csv(csv_output, all_jobs)
    write_json(json_output, all_jobs)
    print(f"Wrote {len(all_jobs)} unique jobs to {csv_output} and {json_output}")


if __name__ == "__main__":
    main()
