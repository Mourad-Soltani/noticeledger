"""Compile a vendor file into page, feed, and notice drafts.

Signature: Mourad.Soltani
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from html import escape
from pathlib import Path

from noticeledger.parser import parse_simple_yaml

REQUIRED_VENDOR = ("name", "purpose", "location", "announced_on", "effective_on", "status")
OPEN_STATUSES = {"pending", "active"}


@dataclass
class Finding:
    vendor: str
    ok: bool
    detail: str


def load_ledger(path: str | Path) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    data = parse_simple_yaml(text)
    company = data.get("company") or {}
    if not company.get("name") or not company.get("privacy_email"):
        raise ValueError("company.name and company.privacy_email are required")
    notice_days = int(data.get("notice_days") or 30)
    vendors = data.get("vendors") or []
    if not isinstance(vendors, list) or not vendors:
        raise ValueError("vendors must be a non-empty list")
    for vendor in vendors:
        missing = [field for field in REQUIRED_VENDOR if not vendor.get(field)]
        if missing:
            raise ValueError(f"{vendor.get('name', '?')} missing {', '.join(missing)}")
        date.fromisoformat(str(vendor["announced_on"]))
        date.fromisoformat(str(vendor["effective_on"]))
    return {"company": company, "notice_days": notice_days, "vendors": vendors}


def check_windows(ledger: dict) -> list[Finding]:
    notice_days = int(ledger["notice_days"])
    findings: list[Finding] = []
    for vendor in ledger["vendors"]:
        announced = date.fromisoformat(str(vendor["announced_on"]))
        effective = date.fromisoformat(str(vendor["effective_on"]))
        earliest = announced + timedelta(days=notice_days)
        if vendor["status"] in OPEN_STATUSES and effective < earliest:
            findings.append(
                Finding(
                    vendor["name"],
                    False,
                    f"effective {effective.isoformat()} is before {earliest.isoformat()}",
                )
            )
        else:
            findings.append(
                Finding(
                    vendor["name"],
                    True,
                    f"window ok ({announced.isoformat()} -> {effective.isoformat()})",
                )
            )
    return findings


def render_json(ledger: dict, findings: list[Finding]) -> str:
    payload = {
        "product": "NoticeLedger",
        "author": "Mourad.Soltani",
        "company": ledger["company"],
        "notice_days": ledger["notice_days"],
        "vendors": ledger["vendors"],
        "findings": [finding.__dict__ for finding in findings],
        "ok": all(finding.ok for finding in findings),
    }
    return json.dumps(payload, indent=2)


def render_html(ledger: dict, findings: list[Finding]) -> str:
    company = ledger["company"]
    rows = []
    by_name = {finding.vendor: finding for finding in findings}
    for vendor in ledger["vendors"]:
        finding = by_name[vendor["name"]]
        flag = "ok" if finding.ok else "short"
        rows.append(
            "<tr>"
            f"<td>{escape(str(vendor['name']))}</td>"
            f"<td>{escape(str(vendor['purpose']))}</td>"
            f"<td>{escape(str(vendor['location']))}</td>"
            f"<td>{escape(str(vendor['status']))}</td>"
            f"<td>{escape(str(vendor['announced_on']))}</td>"
            f"<td>{escape(str(vendor['effective_on']))}</td>"
            f"<td>{flag}</td>"
            "</tr>"
        )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Subprocessors — {escape(str(company['name']))}</title>
  <style>
    body {{ font-family: Georgia, serif; margin: 2rem auto; max-width: 880px; color: #1c1917; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border-bottom: 1px solid #d6d3d1; text-align: left; padding: 0.4rem; }}
  </style>
</head>
<body>
  <p>Signature: Mourad.Soltani</p>
  <h1>Subprocessors</h1>
  <p>{escape(str(company['name']))} publishes this list at least {ledger['notice_days']} days before a new vendor processes personal data.</p>
  <p>Questions: {escape(str(company['privacy_email']))}</p>
  <table>
    <thead><tr><th>Vendor</th><th>Purpose</th><th>Location</th><th>Status</th><th>Announced</th><th>Effective</th><th>Window</th></tr></thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
  <p><a href="feed.xml">RSS changelog</a> · <a href="ledger.json">JSON</a></p>
</body>
</html>
"""


def render_rss(ledger: dict) -> str:
    company = ledger["company"]
    items = []
    for vendor in ledger["vendors"]:
        items.append(
            "<item>"
            f"<title>{escape(str(vendor['name']))} ({escape(str(vendor['status']))})</title>"
            f"<pubDate>{escape(str(vendor['announced_on']))}</pubDate>"
            f"<description>Effective {escape(str(vendor['effective_on']))}. {escape(str(vendor['purpose']))}.</description>"
            "</item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<rss version="2.0"><channel>'
        f"<title>Subprocessors — {escape(str(company['name']))}</title>"
        f"<link>{escape(str(company.get('site', '')))}</link>"
        "<description>NoticeLedger changelog. Signature: Mourad.Soltani</description>"
        + "".join(items)
        + "</channel></rss>"
    )


def render_draft(ledger: dict) -> str:
    company = ledger["company"]
    pending = [v for v in ledger["vendors"] if v["status"] == "pending"]
    lines = [
        f"To: customer-privacy-contact",
        f"From: {company['privacy_email']}",
        f"Subject: Upcoming subprocessor notice — {company['name']}",
        "",
        "This draft was generated by NoticeLedger and has not been sent.",
        "",
        f"{company['name']} plans to authorize the following vendor(s) after the notice window:",
    ]
    if not pending:
        lines.append("- No pending vendors in this file.")
    for vendor in pending:
        lines.append(
            f"- {vendor['name']} ({vendor['purpose']}, {vendor['location']}), "
            f"announced {vendor['announced_on']}, effective {vendor['effective_on']}"
        )
    lines.append("")
    lines.append("Reply to this contact if you need the current public list. Do not bulk-send this file.")
    lines.append("Signature: Mourad.Soltani")
    return "\n".join(lines)


def build(src: str | Path, out: str | Path) -> dict:
    ledger = load_ledger(src)
    findings = check_windows(ledger)
    destination = Path(out)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "index.html").write_text(render_html(ledger, findings), encoding="utf-8")
    (destination / "ledger.json").write_text(render_json(ledger, findings), encoding="utf-8")
    (destination / "feed.xml").write_text(render_rss(ledger), encoding="utf-8")
    (destination / "notice-draft.txt").write_text(render_draft(ledger), encoding="utf-8")
    health = {
        "status": "ok" if all(item.ok for item in findings) else "attention",
        "product": "NoticeLedger",
        "author": "Mourad.Soltani",
        "vendors": len(ledger["vendors"]),
        "generated_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
    }
    (destination / "health.json").write_text(json.dumps(health), encoding="utf-8")
    return health
