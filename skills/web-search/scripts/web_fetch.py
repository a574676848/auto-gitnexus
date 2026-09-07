#!/usr/bin/env python3
"""web-fetch - extract clean page content as Markdown via TinyFish Fetch API.

POST https://api.fetch.tinyfish.ai with X-API-Key. Up to 10 URLs per request;
failed URLs are isolated in errors[] without affecting the rest.
"""

import argparse
import io
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# Force UTF-8 on stdout/stderr regardless of console codepage or pipe redirection.
def _force_utf8(stream):
    if stream is None or stream.encoding is None:
        return stream
    if stream.encoding.lower().replace("-", "") != "utf8":
        return io.TextIOWrapper(stream.buffer, encoding="utf-8", errors="replace", newline="")
    return stream.reconfigure(encoding="utf-8", errors="replace") or stream


sys.stdout = _force_utf8(sys.stdout)
sys.stderr = _force_utf8(sys.stderr)

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENDPOINT = "https://api.fetch.tinyfish.ai"


def load_env():
    def read_env_file(path):
        if not os.path.isfile(path):
            return
        with open(path, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key, value = key.strip(), value.strip().strip("\"'").strip()
                if key and value:
                    os.environ.setdefault(key, value)

    read_env_file(os.path.join(SKILL_DIR, ".env"))
    read_env_file(os.path.join(SKILL_DIR, ".env.qoder"))


load_env()


def build_parser():
    p = argparse.ArgumentParser(
        prog="web_fetch",
        description="Fetch and extract full page content from URLs as clean Markdown "
                    "(or semantic HTML) via the TinyFish Fetch API. Up to 10 URLs per call.",
    )
    p.add_argument("urls", nargs="+", help="One or more URLs (max 10).")
    p.add_argument("--format", choices=["markdown", "html"], default="markdown",
                   help="Output format (default markdown).")
    p.add_argument("--purpose", help="Intent signal: the goal the content will be used for.")
    p.add_argument("--ttl", type=int,
                   help="Max age of an accepted cached copy, in seconds. 0 = live fetch.")
    p.add_argument("--include-selectors", help="Comma-separated CSS selectors; extract only these.")
    p.add_argument("--exclude-selectors", help="Comma-separated CSS selectors; strip these first.")
    p.add_argument("--etag", help="Replay a saved ETag (If-None-Match): if unchanged, response has not_modified=true and text=null.")
    p.add_argument("--if-modified-since", dest="if_modified_since",
                   help="Saved Last-Modified to replay alongside --etag (If-Modified-Since).")
    p.add_argument("--save-validators", action="store_true",
                   help="Include etag/last_modified in output so they can be replayed later.")
    p.add_argument("--max-chars", type=int, default=20000,
                   help="Truncate each page's text to this many characters (default 20000, 0 = no limit).")
    p.add_argument("--timeout", type=int, default=60, help="Request timeout seconds (default 60).")
    p.add_argument("--json", action="store_true", dest="json_output",
                   help="Output machine-readable JSON instead of Markdown.")
    p.add_argument("--quiet", action="store_true", help="Suppress the footer on stderr.")
    return p


def main():
    args = build_parser().parse_args()

    urls = [u.strip() for u in args.urls if u.strip()]
    if not urls:
        print("no URLs given", file=sys.stderr)
        sys.exit(2)
    if len(urls) > 10:
        print(f"{len(urls)} URLs given; the API supports at most 10 per request", file=sys.stderr)
        sys.exit(2)

    api_key = os.environ.get("TINYFISH_API_KEY", "")
    if not api_key:
        print(json.dumps({"success": False, "error": "TINYFISH_API_KEY not configured (missing key)"}))
        sys.exit(1)

    body = {"urls": urls, "format": args.format}
    if args.purpose:
        body["purpose"] = args.purpose
    if args.ttl is not None:
        body["ttl"] = args.ttl
    if args.include_selectors:
        body["include_selectors"] = [s.strip() for s in args.include_selectors.split(",") if s.strip()]
    if args.exclude_selectors:
        body["exclude_selectors"] = [s.strip() for s in args.exclude_selectors.split(",") if s.strip()]
    if args.save_validators:
        body["include_etag_and_last_modified"] = True
    if args.etag:
        body["if_none_match"] = args.etag
    if args.if_modified_since:
        body["if_modified_since"] = args.if_modified_since

    req = urllib.request.Request(
        ENDPOINT, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-API-Key": api_key},
        method="POST",
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print(f"{type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
    elapsed_ms = int((time.time() - t0) * 1000)

    pages, errors = data.get("results", []), data.get("errors", [])
    for page in pages:
        if args.max_chars > 0:
            page["text"] = (page.get("text") or "")[:args.max_chars]

    if args.json_output:
        print(json.dumps({"success": not not pages, "elapsed_ms": elapsed_ms,
                          "pages": pages, "errors": errors}, ensure_ascii=False, indent=2))
    else:
        print(f"# Web Fetch: {len(pages)} page(s), {len(errors)} error(s), {elapsed_ms}ms")
        for page in pages:
            print()
            print(f"## {page.get('title') or page.get('url')}")
            print(f"- **URL**: {page.get('url')}")
            if page.get("final_url") and page["final_url"] != page["url"]:
                print(f"- **Final URL**: {page['final_url']}")
            meta = []
            if page.get("language"):
                meta.append(f"**Language**: {page['language']}")
            if page.get("author"):
                meta.append(f"**Author**: {page['author']}")
            if page.get("published_date"):
                meta.append(f"**Published**: {page['published_date']}")
            if page.get("latency_ms"):
                meta.append(f"**Latency**: {int(float(page['latency_ms']))}ms")
            if meta:
                print("- " + " | ".join(meta))
            if page.get("not_modified"):
                print("- **Unchanged** since last fetch (etag replay): content skipped.")
                continue
            if page.get("unmatched_selectors"):
                print(f"- **Unmatched selectors**: {', '.join(page['unmatched_selectors'])}")
            print()
            print(page.get("text") or "(empty page)")
        for err in errors:
            print()
            print(f"## ERROR: {err.get('url')}")
            print(f"> {err.get('error')} (HTTP {err.get('status', '?')})")

    if not args.quiet:
        print(f"\n[web-fetch] {len(pages)} ok, {len(errors)} failed, {elapsed_ms}ms", file=sys.stderr)


if __name__ == "__main__":
    main()
