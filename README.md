# NoticeLedger

Signature: Mourad.Soltani

NoticeLedger is a solo-sized micro tool for SaaS founders who must publish a
subprocessor list and give customers a dated notice window before a new vendor
starts processing personal data.

It reads one YAML file, checks the notice window, and writes:

- a public HTML page
- a JSON document
- an RSS changelog
- a one-to-one customer notice draft (not sent)

No account, no database, no outbound email.

## Why this exists

GDPR-style DPAs commonly require about 30 days of notice before a new
subprocessor is authorized. Most early-stage teams keep that list in a doc.
NoticeLedger makes the list, the clock, and the draft reviewable in one command.

## Quick start

```bash
python3 -m noticeledger build examples/vendors.yaml --out dist
python3 -m noticeledger serve dist --port 8080
curl -s localhost:8080/health
```

Open `http://localhost:8080/` for the public page.

## Vendor file

```yaml
company:
  name: Northwind Analytics
  site: https://northwind.example
  privacy_email: privacy@northwind.example
notice_days: 30
vendors:
  - name: Stripe
    purpose: Subscription billing
    location: United States
    announced_on: 2026-01-02
    effective_on: 2026-02-02
    status: active
```

`effective_on` must be at least `notice_days` after `announced_on` when status
is `pending` or `active`. `retired` vendors are listed but do not open a new
window.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Buyer notes

See `BUYER_NOTES.md`. One-to-one outreach drafts live in `OUTREACH.md`.
This repository does not send email.
