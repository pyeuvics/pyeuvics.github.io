# Frontend behavior checks

Run from the repository root with the declared Python environment active and
Node 24 available:

```bash
npm ci --ignore-scripts
npx playwright install chromium
npm run test:browser
```

On a fresh Linux runner, use `npx playwright install --with-deps chromium` to
install system libraries too. Installation needs public package/browser network
access. Test execution uses a disposable loopback server and public synthetic
fixtures; it does not read private repositories or use credentials. Do not run
against a personal browser profile. The server refuses an occupied port and
Playwright closes it after the suite. Browser traces on failure remain under
ignored `.staging/browser-results/`; they contain only synthetic pages.

## Tooling decision — 2026-10-10

Use Playwright **1.64.0**, its bundled Chromium revision, Node **24**, and the
same exact MathJax **3.2.2** package as the site's CDN pin. `package-lock.json`
records all resolved dependencies and integrity values; `npm ci --ignore-scripts`
avoids lifecycle scripts. These are test dependencies, separate from Python
numerical and document environments. The required `Validate website source`
job runs this layer after the Python quality command with the existing read-only
permissions. Browser results are separate from the reusable Python quality
receipt; that receipt does not claim a browser run. Trusted assembly remains
independently gated by source contracts and artifact checks.

The fixture server strictly builds the scaffold and a synthetic assembly with
an approved PDF, notebook and campaign. Browser routing fulfills the exact CDN
MathJax requests from its installed package, including fonts, and blocks other
external requests. It permits loopback HTTP and maps canonical 404 assets to the
same local site. Thus the suite does not depend on live fonts, GitHub APIs,
private content, the real CDN, or a deployed site. It verifies actual MathJax
output as well as controlled delayed-load/error behavior.

Behavior assertions cover desktop and mobile keyboard routes, drawer state and
focus restoration, search result navigation, repeated initialization, equation
rendering and recovery, headings, image alternative text/caption relationships,
PDF bytes and displayed checksums, notebook content, narrow overflow, CSS zoom,
computed focus contrast, reduced motion, print and custom 404 HTTP responses.
They use bounded waits and no screenshot baselines or automatic retries.
Scientific wording/conventions and source ownership remain separately tested.

## Limits and release review

A Chromium viewport/zoom test is not a cross-browser or assistive-technology
certification. The local 404 server is a fixture, not proof of Pages routing.
The real CDN and signed-out hosted accessibility review remain separate manual
release checks: record URL, deployed commit, browser/device, keyboard/search,
zoom, equations, downloads, 404, and review date. **No hosted signed-out review
was performed by this refactoring.** Test success is not publication approval.

When updating tooling, review [Playwright's CLI](https://playwright.dev/docs/test-cli),
the package licenses, npm lock diff, browser revision and
[MathJax delivery policy](browser-lifecycle.md). Run both local fixture variants
and inspect failure evidence before changing any pin or tolerance.
