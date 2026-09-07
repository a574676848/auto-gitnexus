#!/usr/bin/env python3
"""web-search skill - 4-way parallel web search (Bing RSS / AnySearch / TinyFish / Tavily)."""

import argparse
import concurrent.futures
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

# Force UTF-8 on stdout/stderr regardless of console codepage or pipe redirection.
# On Windows the default is the ANSI codepage (GBK on zh-CN), which mangles output
# once it's piped or redirected. errors="replace" keeps unencodable chars from crashing.
def _force_utf8(stream):
    if stream is None or stream.encoding is None:
        return stream
    if stream.encoding.lower().replace("-", "") != "utf8":
        return io.TextIOWrapper(stream.buffer, encoding="utf-8", errors="replace", newline="")
    return stream.reconfigure(encoding="utf-8", errors="replace") or stream


sys.stdout = _force_utf8(sys.stdout)
sys.stderr = _force_utf8(sys.stderr)

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_env():
    """Priority: env var > skill .env > project .env.qoder"""
    def read_env_file(path):
        if not os.path.isfile(path):
            return
        with open(path, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("\"'").strip()
                if key and value:
                    os.environ.setdefault(key, value)

    read_env_file(os.path.join(SKILL_DIR, ".env"))
    read_env_file(os.path.join(SKILL_DIR, ".env.qoder"))


load_env()


def http_get(url, headers=None, timeout=15):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def http_post_json(url, body, headers=None, timeout=20):
    data = json.dumps(body).encode("utf-8")
    hdrs = {"Content-Type": "application/json", "User-Agent": USER_AGENT}
    hdrs.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=hdrs, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


# ---------------- providers ----------------

def norm_result(source, title, url, snippet, rank, extra=None):
    r = {
        "source": source,
        "rank": rank,
        "title": (title or "").strip(),
        "url": (url or "").strip(),
        "snippet": (snippet or "").strip(),
    }
    if extra:
        r.update(extra)
    return r


def search_bing(query, top_n, opt, timeout):
    """Bing RSS: GET https://www.bing.com/search?q=...&format=rss (free, no key).

    Known caveats: `count` is unreliable (server decides); `ensearch=1` enforces
    international results; region comes from the exit IP and cannot be fully
    controlled server-side.
    """
    params = {"q": query, "format": "rss", "count": str(top_n)}
    if opt.get("market"):
        params["mkt"] = opt["market"]
        params["setlang"] = opt["market"].split("-")[0]
    url = "https://www.bing.com/search?" + urllib.parse.urlencode(params)
    xml_bytes = http_get(url, timeout=timeout)
    root = ET.fromstring(xml_bytes)
    results = []
    for i, item in enumerate(root.iter("item"), 1):
        if i > top_n:
            break
        results.append(norm_result(
            "bing", item.findtext("title", ""), item.findtext("link", ""),
            item.findtext("description", ""), i,
        ))
    return results


def search_anysearch(query, top_n, opt, timeout):
    """AnySearch: JSON-RPC 2.0 at https://api.anysearch.com/mcp. Key optional."""
    api_key = os.environ.get("ANYSEARCH_API_KEY", "")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = "Bearer " + api_key
    payload = {
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "search", "arguments": {"query": query, "max_results": min(top_n, 10)}},
    }
    data = http_post_json("https://api.anysearch.com/mcp", payload, headers=headers, timeout=timeout)
    text = ""
    for item in data.get("result", {}).get("content", []):
        if item.get("type") == "text":
            text = item.get("text", "")
            break
    results = []
    # Output is Markdown; entries look like "### N. Title" followed by "- **URL**: <url>"
    blocks = re.split(r"(?=^###\s)", text, flags=re.MULTILINE)
    for block in blocks:
        m_title = re.match(r"###\s*\d+\.\s*(.+)", block)
        if not m_title:
            continue
        m_url = re.search(r"\*\*URL\*\*:\s*(\S+)", block)
        snippet = ""
        m_snip = re.search(r"(?:\n|\s)-\s(.+)", block.split("URL**:", 1)[-1], flags=re.S)
        if m_snip:
            snippet = m_snip.group(1).strip()
        if m_url:
            results.append(norm_result(
                "anysearch", m_title.group(1).strip(), m_url.group(1).strip(), snippet, len(results) + 1,
            ))
        if len(results) >= top_n:
            break
    return results


def search_tinyfish(query, top_n, opt, timeout):
    """TinyFish: GET https://api.search.tinyfish.ai with X-API-Key header."""
    api_key = os.environ.get("TINYFISH_API_KEY", "")
    if not api_key:
        raise RuntimeError("TINYFISH_API_KEY not configured (missing key)")
    params = {"query": query}
    if opt.get("location"):
        params["location"] = opt["location"]
    if opt.get("purpose"):
        params["purpose"] = opt["purpose"]
    if opt.get("language"):
        params["language"] = opt["language"]
    if opt.get("include_domains"):
        params["include_domains"] = opt["include_domains"]
    if opt.get("exclude_domains"):
        params["exclude_domains"] = opt["exclude_domains"]
    if opt.get("domain_type"):
        params["domain_type"] = opt["domain_type"]
    elif opt.get("news"):
        params["domain_type"] = "news"
    if opt.get("page"):
        params["page"] = opt["page"]
    if opt.get("recency_minutes"):
        params["recency_minutes"] = opt["recency_minutes"]
    if opt.get("after_date"):
        params["after_date"] = opt["after_date"]
    if opt.get("before_date"):
        params["before_date"] = opt["before_date"]
    if opt.get("pub_year_min"):
        params["pub_year_min"] = opt["pub_year_min"]
    if opt.get("pub_year_max"):
        params["pub_year_max"] = opt["pub_year_max"]
    url = "https://api.search.tinyfish.ai?" + urllib.parse.urlencode(params)
    data = json.loads(http_get(url, headers={"X-API-Key": api_key}, timeout=timeout).decode("utf-8", "replace"))
    results = []
    for item in data.get("results", [])[:top_n]:
        extra = {"site_name": item.get("site_name", "")}
        for k in ("publisher", "date", "authors", "venue", "year", "cited_by_count", "pdf_url"):
            if item.get(k):
                extra[k] = item[k]
        results.append(norm_result(
            "tinyfish", item.get("title", ""), item.get("url", ""),
            item.get("snippet", ""), item.get("position", len(results) + 1), extra,
        ))
    return results


def search_tavily(query, top_n, opt, timeout):
    """Tavily: POST https://api.tavily.com/search, Bearer auth."""
    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY not configured (missing key)")
    body = {"query": query, "max_results": min(top_n, 20)}
    if opt.get("depth") == "advanced":
        body["search_depth"] = "advanced"
    if opt.get("news"):
        body["topic"] = "news"
    if opt.get("answer"):
        body["include_answer"] = True
    if opt.get("time_range"):
        body["time_range"] = opt["time_range"]
    if opt.get("after_date"):
        body["start_date"] = opt["after_date"]
    if opt.get("before_date"):
        body["end_date"] = opt["before_date"]
    if opt.get("include_domains"):
        body["include_domains"] = [d.strip() for d in opt["include_domains"].split(",") if d.strip()]
    if opt.get("exclude_domains"):
        body["exclude_domains"] = [d.strip() for d in opt["exclude_domains"].split(",") if d.strip()]
    data = http_post_json(
        "https://api.tavily.com/search", body,
        headers={"Authorization": "Bearer " + api_key}, timeout=timeout,
    )
    if "results" not in data and data.get("detail"):
        raise RuntimeError("Tavily API error: " + json.dumps(data["detail"], ensure_ascii=False))
    answer = data.get("answer") or ""
    results = []
    for i, item in enumerate(data.get("results", [])[:top_n], 1):
        extra = {}
        if item.get("score") is not None:
            extra["score"] = round(float(item["score"]), 3)
        if item.get("published_date"):
            extra["published_date"] = item["published_date"]
        results.append(norm_result(
            "tavily", item.get("title", ""), item.get("url", ""),
            (item.get("content") or "")[:500], i, extra,
        ))
    return {"results": results, "answer": answer} if answer else results


PROVIDERS = {
    "bing": search_bing,
    "anysearch": search_anysearch,
    "tinyfish": search_tinyfish,
    "tavily": search_tavily,
}


# ---------------- merge & dedupe ----------------

def _norm_url_for_dedupe(url):
    u = url.strip().lower()
    u = re.sub(r"^https?://(www\.)?", "", u)
    u = u.rstrip("/") or u
    return u.split("#", 1)[0]


def merge_results(per_provider, top_n):
    """Dedupe by normalized URL, score by (hit count, sum of reciprocal ranks).

    A URL found by 2+ providers is strong consensus signal and ranks above a
    URL found by only one, regardless of single-provider rank.
    """
    merged = {}
    for provider, results in per_provider.items():
        for r in results:
            key = _norm_url_for_dedupe(r["url"])
            if not key:
                continue
            if key not in merged:
                merged[key] = {"hits": [], "rr": 0.0}
            merged[key]["hits"].append({"provider": provider, "rank": r["rank"]})
            merged[key]["rr"] += 1.0 / (r["rank"] + 1)

    candidates = []
    for key, info in merged.items():
        sources = sorted({h["provider"] for h in info["hits"]})
        best_rank = min(h["rank"] for h in info["hits"])
        candidates.append({
            "key": key, "sources": sources, "source_count": len(sources),
            "best_rank": best_rank, "rr": info["rr"],
        })
    candidates.sort(key=lambda c: (-c["source_count"], -c["rr"], c["best_rank"]))

    # pick one representative result per URL (prefer the entry with the longest snippet)
    output = []
    for c in candidates[:top_n]:
        rep, rep_len = None, -1
        for provider in c["sources"]:
            for r in per_provider[provider]:
                if _norm_url_for_dedupe(r["url"]) == c["key"]:
                    if len(r["snippet"]) > rep_len:
                        rep, rep_len = r, len(r["snippet"])
        if rep:
            entry = dict(rep)
            entry["sources"] = c["sources"]
            entry["source_count"] = c["source_count"]
            entry["merged_rank"] = len(output) + 1
            output.append(entry)
    return output


# ---------------- CLI ----------------

def build_parser():
    p = argparse.ArgumentParser(
        prog="web_search",
        description="4-way parallel web search: Bing RSS / AnySearch / TinyFish / Tavily, "
                    "deduped and consensus-ranked. Default output is agent-friendly Markdown; "
                    "use --json for the machine-readable JSON object.",
    )
    p.add_argument("query", help="Search query (quoted).")
    p.add_argument("--top", type=int, default=10, help="Merged results to return after dedup (default 10).")
    p.add_argument("--per-provider", type=int, default=10,
                   help="Max results requested from each provider (default 10).")
    p.add_argument("--providers", default="bing,anysearch,tinyfish,tavily",
                   help="Comma-separated subset: bing,anysearch,tinyfish,tavily (default all).")
    p.add_argument("--timeout", type=int, default=20, help="Per-provider timeout seconds (default 20).")
    p.add_argument("--news", action="store_true",
                   help="News mode: Tavily topic=news, TinyFish domain_type=news.")
    p.add_argument("--market", default=None,
                   help="Bing market, e.g. en-US / zh-CN. Strongly recommended: region comes "
                        "from exit IP and is otherwise unpredictable.")
    p.add_argument("--location", help="TinyFish country code, e.g. US.")
    p.add_argument("--language", help="TinyFish language code, e.g. en / zh.")
    p.add_argument("--depth", choices=["basic", "advanced"], help="Tavily search_depth (advanced = 2 credits).")
    p.add_argument("--include-domains", help="Comma-separated domain whitelist (TinyFish/Tavily).")
    p.add_argument("--exclude-domains", help="Comma-separated domain blacklist (TinyFish/Tavily).")
    p.add_argument("--purpose", help="TinyFish intent signal: why you are searching.")
    p.add_argument("--domain-type", choices=["news", "research_paper"],
                   help="TinyFish vertical domain (news adds publisher/date; research_paper adds "
                        "authors/venue/year/cited_by_count/pdf_url).")
    p.add_argument("--page", type=int, help="TinyFish result page (0-based; fetch deeper pages).")
    p.add_argument("--recency-minutes", type=int,
                   help="TinyFish freshness window in minutes relative to now (e.g. 60 = last hour).")
    p.add_argument("--after-date", help="Calendar lower bound YYYY-MM-DD (TinyFish after_date / Tavily start_date).")
    p.add_argument("--before-date", help="Calendar upper bound YYYY-MM-DD (TinyFish before_date / Tavily end_date).")
    p.add_argument("--pub-year-min", type=int, help="TinyFish research_paper min publication year (inclusive).")
    p.add_argument("--pub-year-max", type=int, help="TinyFish research_paper max publication year (inclusive).")
    p.add_argument("--time-range", choices=["day", "week", "month", "year"],
                   help="Tavily relative freshness window (day/week/month/year).")
    p.add_argument("--answer", action="store_true",
                   help="Ask Tavily for an LLM-generated direct answer to the query (include_answer).")
    p.add_argument("--json", action="store_true", dest="json_output",
                   help="Output the machine-readable JSON object instead of Markdown.")
    p.add_argument("--raw", action="store_true",
                   help="Also print per-provider raw results under providers[].results.")
    p.add_argument("--quiet", action="store_true", help="Suppress the human-readable footer on stderr.")
    return p


def render_markdown(out):
    """Agent-facing default view: consensus stars, per-result meta, provider health."""
    lines = []
    lines.append(f"# Web Search: {out['query']}")
    lines.append("")
    meta = [f"{out['total_results']} results", f"{out['elapsed_ms']}ms"]
    ok = [p for p in out["providers"] if p["status"] == "ok"]
    failed = [p for p in out["providers"] if p["status"] == "error"]
    meta.append(f"{len(ok)}/{len(out['providers'])} engines ok ({'+'.join(p['name'] for p in ok) or 'none'})")
    lines.append("*" + " | ".join(meta) + "*")
    lines.append("")

    if failed:
        for p in failed:
            lines.append(f"> engine `{p['name']}` failed: {p['error']}")
        lines.append("")

    if out.get("answer"):
        lines.append("## AI Answer (Tavily)")
        lines.append("")
        lines.append(out["answer"])
        lines.append("")

    lines.append("## Results")
    lines.append("")
    for r in out["results"]:
        stars = "*" * r["source_count"] + "-" * (4 - r["source_count"])
        lines.append(f"### {r['merged_rank']}. {r['title'] or r['url']}")
        lines.append(f"- **URL**: {r['url']}")
        lines.append(f"- **Consensus**: {stars} hit by {'+'.join(r['sources'])}"
                     f" (best rank {r['rank']} at {r['source']})")
        info = []
        for k, label in (("published_date", "Published"), ("date", "Date"), ("publisher", "Publisher"),
                         ("site_name", "Site"), ("year", "Year"), ("venue", "Venue"),
                         ("cited_by_count", "Citations"), ("score", "Score")):
            if r.get(k):
                info.append(f"**{label}**: {r[k]}")
        if info:
            lines.append("- " + " | ".join(info))
        if r.get("authors"):
            lines.append(f"- **Authors**: {', '.join(r['authors']) if isinstance(r['authors'], list) else r['authors']}")
        if r.get("pdf_url"):
            lines.append(f"- **PDF**: {r['pdf_url']}")
        snippet = (r.get("snippet") or "").strip()
        if snippet:
            lines.append("")
            lines.append(f"> {snippet}")
        lines.append("")
    src_summary = ", ".join(f"{p['name']}({p['result_count']})" for p in out["providers"])
    lines.append("---")
    lines.append(f"*Engines: {src_summary}*")
    return "\n".join(lines)


def main():
    args = build_parser().parse_args()
    opt = vars(args)

    selected = [p.strip() for p in args.providers.split(",") if p.strip()]
    unknown = [p for p in selected if p not in PROVIDERS]
    if unknown:
        print(json.dumps({"success": False, "error": "unknown providers: " + ",".join(unknown)}), file=sys.stderr)
        sys.exit(2)

    def run_one(name):
        t0 = time.time()
        try:
            ret = PROVIDERS[name](args.query, args.per_provider, opt, args.timeout)
            if isinstance(ret, dict) and "results" in ret:  # Tavily answer payload
                results, answer = ret["results"], ret["answer"]
            else:
                results, answer = ret, ""
            return name, {"results": results, "answer": answer,
                         "elapsed_ms": int((time.time() - t0) * 1000), "error": None}
        except Exception as e:  # noqa: BLE001 - report per-provider failure, don't kill the batch
            return name, {"results": [], "answer": "",
                         "elapsed_ms": int((time.time() - t0) * 1000),
                         "error": f"{type(e).__name__}: {e}"}

    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(selected)) as pool:
        futures = {pool.submit(run_one, name): name for name in selected}
        per_provider = {}
        for fut in concurrent.futures.as_completed(futures):
            name, payload = fut.result()
            per_provider[name] = payload
    total_ms = int((time.time() - t0) * 1000)

    merged = merge_results({k: v["results"] for k, v in per_provider.items()}, args.top)
    answer = next((v["answer"] for v in per_provider.values() if v["answer"]), "")

    out = {
        "success": True,
        "query": args.query,
        "total_results": len(merged),
        "elapsed_ms": total_ms,
        "answer": answer,
        "results": merged,
        "providers": [
            {
                "name": name,
                "status": "error" if per_provider[name]["error"] else "ok",
                "result_count": len(per_provider[name]["results"]),
                "elapsed_ms": per_provider[name]["elapsed_ms"],
                "error": per_provider[name]["error"],
            }
            for name in selected
        ],
    }
    if args.raw:
        for entry in out["providers"]:
            entry["results"] = per_provider[entry["name"]]["results"]

    if args.json_output:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(out))

    if not args.quiet:
        ok_count = sum(1 for e in out["providers"] if e["status"] == "ok")
        print(f"\n[web-search] {ok_count}/{len(selected)} providers ok, "
              f"{len(merged)} merged results, {total_ms}ms total", file=sys.stderr)


if __name__ == "__main__":
    main()
