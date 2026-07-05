"""The watcher engine: fetch a watched source, normalise it, fingerprint
it, and raise a ChangeAlert when it differs from the last check.

Deliberately semi-automated (architecture doc §5.4): this module only
detects and diffs. It never touches TaxParameter, Strategy, or Authority
rows. The fetcher is injectable so tests (and future feed-specific
watchers, e.g. the legislation.gov.uk XML API or HMRC manual change logs)
can plug in without changing the pipeline.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import re
import urllib.request
from urllib.parse import urlparse

from django.utils import timezone

from .models import ChangeAlert, WatchedSource

USER_AGENT = "KAFS-TaxPlanner-watcher/1.0 (rule-base change monitoring)"
DIFF_MAX_LINES = 80

_TAG_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
_HTML_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t\f\v]+")


def http_get(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def default_fetcher(url: str) -> str:
    return http_get(url)


# --- Feed-specific fetchers ---------------------------------------------------
# Structured feeds give cleaner text than scraping rendered pages, so a
# styling change on the website can never look like a change in the law.
# Every feed fetcher falls back to the plain page if the feed errors —
# a degraded check beats a missed check.


def fetch_legislation(url: str, http=http_get) -> str:
    """legislation.gov.uk exposes every provision as XML at <uri>/data.xml
    (The National Archives' API — architecture doc Appendix)."""
    try:
        return http(url.rstrip("/") + "/data.xml")
    except Exception:
        return http(url)


def fetch_govuk_content(url: str, http=http_get) -> str:
    """gov.uk (including HMRC manuals) exposes structured JSON at
    /api/content/<path>; the details payload carries the substantive body
    without site chrome."""
    parsed = urlparse(url)
    if parsed.netloc.endswith("gov.uk"):
        try:
            raw = http(f"{parsed.scheme}://{parsed.netloc}/api/content{parsed.path}")
            payload = json.loads(raw)
            details = payload.get("details", {})
            return json.dumps(details, ensure_ascii=False, indent=0, sort_keys=True)
        except Exception:
            pass
    return http(url)


def resolve_fetcher(source: WatchedSource, http=http_get):
    """Pick the feed-appropriate fetcher for a source type."""
    if source.source_type == WatchedSource.SourceType.LEGISLATION:
        return lambda url: fetch_legislation(url, http=http)
    if source.source_type == WatchedSource.SourceType.HMRC_MANUAL:
        return lambda url: fetch_govuk_content(url, http=http)
    return http


def normalise(raw: str) -> str:
    """Strip markup and collapse whitespace so cosmetic page changes
    (styling, layout) don't raise false alerts — only text changes do."""
    text = _TAG_RE.sub(" ", raw)
    text = _HTML_RE.sub(" ", text)
    lines = [_WS_RE.sub(" ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def check_source(source: WatchedSource, fetcher=None) -> ChangeAlert | None:
    """Check one source. Returns the ChangeAlert if a change was detected,
    None otherwise. First-ever check just baselines the content. When no
    explicit fetcher is given, the feed-appropriate one for the source
    type is used (legislation XML API, gov.uk content API, plain HTML)."""
    if fetcher is None:
        fetcher = resolve_fetcher(source)
    text = normalise(fetcher(source.url))
    new_fp = fingerprint(text)

    alert = None
    if source.last_fingerprint and new_fp != source.last_fingerprint:
        diff = difflib.unified_diff(
            source.last_content_snapshot.splitlines(),
            text.splitlines(),
            fromfile="previous",
            tofile="current",
            lineterm="",
        )
        diff_lines = list(diff)[:DIFF_MAX_LINES]
        alert = ChangeAlert.objects.create(
            source=source,
            previous_fingerprint=source.last_fingerprint,
            new_fingerprint=new_fp,
            diff_excerpt="\n".join(diff_lines),
        )

    source.last_checked_at = timezone.now()
    source.last_fingerprint = new_fp
    source.last_content_snapshot = text
    source.save(update_fields=["last_checked_at", "last_fingerprint", "last_content_snapshot"])
    return alert


def run_all(fetcher=default_fetcher) -> dict:
    """Check every active source; skip (and report) fetch failures rather
    than aborting the run — a dead link is itself worth knowing about."""
    summary = {"checked": 0, "baselined": 0, "alerts": 0, "errors": []}
    for source in WatchedSource.objects.filter(active=True):
        had_baseline = bool(source.last_fingerprint)
        try:
            alert = check_source(source, fetcher=fetcher)
        except Exception as exc:  # noqa: BLE001 — record and continue
            summary["errors"].append(f"{source.label}: {exc}")
            continue
        summary["checked"] += 1
        if not had_baseline:
            summary["baselined"] += 1
        if alert is not None:
            summary["alerts"] += 1
    return summary
