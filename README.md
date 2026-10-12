# GOODRAM Tender Intelligence v1.4.1 RC

Release candidate for Render deployment and connector testing.

## Production connectors
TED, Prozorro, BZP Poland, Germany OCDS, EKAP Turkey (APIFY_API_TOKEN), Latvia IUB Open Data.

## Beta connectors
Czech NEN, Slovakia UVO/EVO, Lithuania CVP IS, Hungary EKR, Estonia RHR discovery.

## Diagnostics
Every connector reports status, parsed/scanned counts and a bounded error/traceback excerpt. Estonia deliberately reports a discovery error when no public JSON feed is found. Secrets are not logged.

## Render variable
`APIFY_API_TOKEN` is required only for EKAP Turkey. Translation variables remain optional.
