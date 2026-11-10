# Validation record — 10 November 2026

## Executed successfully

- Python dependency installation and `pip check` (Waitress 3.0.2).
- 15 backend integration tests against a real temporary SQLite database and HTTP server: authentication, logout, cross-origin rejection, authorization, project/file isolation, uploads, review-state approval, booking contention, authoritative pricing, enquiry persistence, honest provider states, reset-token consumption, public publication and throttling.
- Browser end-to-end workflow on Chromium against both the local runner and the Waitress WSGI server. Final WSGI run covered pricing comparison, submitted enquiries, persistent briefs, registration, saved estimates, administrator-published portfolio records, project search, milestones, feedback, uploads, real reservation writes, simulator controls, feature demos, viewing preferences, FAQ fallback, health errors, published journal entries, Easter egg, mobile layouts at 390px and enlarged text, and logout.
- Original UI regression smoke test: initial Vision Lab handoff, history, persisted theme, mobile navigation, reduced motion, both entry points, contact validation and mandatory consent. This check does not submit a real enquiry.
- Read-only requests to the running WSGI server: `/`, `/api/config`, `/api/session`, `/api/showcase` returned 200.
- JavaScript syntax checks, Python compilation, identical HTML entry points and `git diff --check`.
- Desktop pricing and mobile transformation screenshots inspected.
- Axe-core WCAG 2 A/AA automated checks on pricing, Explore, Vision Lab, sign-in and services found no violations after transitions settled, in both dark and light themes. This is a scoped automated check, not a complete accessibility certification.
- MTDI Studio's tracked/untracked status checked read-only and remained clean.

## External limitations

- Instagram reference requests: proxy 403 on all eight reels; no video frames were observed.
- Real PageSpeed request: failed because public DNS resolution is unavailable; a direct request to Google's endpoint also returned proxy 403. The UI/API returns an error with no scores. Successful Lighthouse parsing is covered by a labelled fixture, not a claimed live audit.
- No Gemini key is configured. The deterministic FAQ fallback was exercised; successful live Gemini generation has not been verified.
- SMTP credentials are not configured. Enquiry persistence and `not_configured` delivery responses were verified. Real email delivery and password-reset email delivery were not attempted; token behavior is tested with a mocked sender.
- No public deployment, real client project, production administrator password, production meeting availability or public announcement was created.

The environment configuration draft includes NVTRA installation/startup instructions, the Gemini key requirement, and Google API destination additions. Saving the draft does not inject a key, apply networking or publish the environment.

## Cinematic design verification

The new design passed 15 backend tests, the complete isolated Waitress browser workflow, and the existing UI regression suite. A dedicated browser suite verified the WebGL sculpture and unavailable-WebGL fallback, exhibition navigation, study region controls, five process stages, seven new brief settings and session persistence, custom 3D scope, package exploration, 768px/390px layouts, mobile preview jumps and reduced motion. Desktop homepage, exhibition, Vision Lab and mobile homepage renders were inspected. No live client records were created.

A save/dashboard timing issue found during regression testing was fixed by refreshing an already-open dashboard when a save completes. Automated contrast checks also prompted corrections to the original homepage’s pale information section.

## Free hosting and standalone preview

The paid Render Blueprint, startup code, instructions and associated tests were removed. The replacement free-host WSGI generator rejects unrelated domains and public storage paths, supports the provider’s US/EU free domains and refuses to overwrite an existing output. Its generated entry point was run locally with `python -S` (third-party packages disabled), served `/api/config`, initialized an isolated private database and emitted HTTPS security headers.

20 backend/setup/export tests passed, together with the complete isolated Waitress browser workflow. The standalone preview browser test ran with every external network request blocked and no backend: pricing, brief customization/downloads, enquiry email preparation/download, search, local FAQ, explicit disabled authentication, the external PageSpeed link, and mobile layouts passed. It made zero API requests. Desktop and mobile preview renders were inspected. The managed Chromium policy blocks `file://` navigation in this workspace, so the self-contained HTML was supplied directly to the test browser at an intercepted static origin; opening a downloaded file on the user's device has not been tested here.

PythonAnywhere’s free-account and CPU-limit documentation was read from its official Git repository at commit `3872b734cfb44d5df1082d9afbe054dd53884f70`. Direct HTTP access to PythonAnywhere, GitHub’s API, GitHub Pages and the external preview viewer is blocked by this workspace's network proxy. Repository pushes through Git work. No PythonAnywhere service or GitHub Pages deployment has been claimed as live or verified. The user is creating a free hosting account; live accounts, external Gemini, SMTP delivery and live PageSpeed results still need verification on that host.

## Vercel deployment correction

Added an explicit framework-free Vercel build/output configuration and deployment exclusions. `node tests/vercel.cjs` built the real deployment artifact, verified its public-files-only output and exercised its estimator, brief downloads, enquiry email preparation, search, FAQ, disabled login, health-check link and mobile layouts with zero API requests. The original backend application remains separate and unchanged. Direct requests to the user’s Vercel homepage and API endpoints were blocked by the workspace proxy; the deployed response and deployment completion could not be verified here.
