---
name: testing-ihsg-static-app
description: Test the static IHSG Fear & Greed app locally, including calculator UI flows. Use when verifying frontend changes in this repo.
---

# Testing IHSG Fear & Greed Static App

## Devin Secrets Needed

No secrets are needed for local static UI testing. Public Vercel previews may be available on PR comments, but local testing does not require Vercel credentials.

## Setup

1. From the repo root, validate JavaScript syntax when `assets/app.js` changes:
   ```bash
   node --check assets/app.js
   ```
2. Build the static output:
   ```bash
   npm run build
   ```
3. Serve the built app from `public/` on an unused port:
   ```bash
   python3 -m http.server 8024 --directory public
   ```
4. Open Chrome to the route being tested, for example:
   ```text
   http://localhost:8024/#/calculator
   ```

## Calculator Testing Notes

- The calculator page is hash-routed at `#/calculator`.
- Use the visible calculator selector tabs instead of console/devtools shortcuts.
- For Right Issue changes, click the `Right Issue` tab and verify concrete rows in the result grid.
- A useful dilution sanity check is `Lot Saat Ini = 10`, `Rasio Lama = 2`, `Rasio Baru = 1`; expected dilution is `33.33% (porsi jadi 66.67%)`.
- A no-new-share edge check is `Rasio Baru = 0`; expected dilution is `0.00% (porsi jadi 100.00%)`.

## Evidence

For UI PRs, record the browser flow and include screenshots in the test report. Keep the recording focused on the changed route and annotate the main assertion points.
