# Running NVTRA

## Local workflow

Use the existing `/workspace/nvtra` checkout. MTDI Studio is read-only: do not edit its source, dependency environment or runtime state. No worktree is needed.

```sh
cd /workspace/nvtra
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/waitress-serve --listen=127.0.0.1:8080 --threads=8 --max-request-body-size=7340032 app:application
```

The default public origin is `http://127.0.0.1:8080`. If using another address or port, set `NVTRA_PUBLIC_URL` to that exact origin before starting. Mutating requests must originate from it. `python server.py --port 8080` is an alternative local development runner. Static-only hosting no longer supports the application's accounts and forms.

`GET /api/config`, `GET /api/session`, and the homepage should return 200. Account registration, pricing, briefs, enquiries, private projects, local meeting reservations, search and FAQ support do not need paid external services.

## Studio administration

Create an administrator locally, with an interactive password prompt:

```sh
.venv/bin/python server.py --create-admin nvtra.official@icloud.com
```

Use the same `NVTRA_DATA_DIR` for this command and the running server. Passwords must be at least 12 characters. Do not paste passwords into chat or commit them. This command can also recover a studio administrator account; it invalidates existing sessions for that account.

Sign in, open My studio → Studio operations. The administrator can:

- Review stored enquiries, briefs, estimates and email status.
- Assign an accepted project to an existing client account by its explicit ID. Confirm the person's identity first; registration alone does not verify ownership of their email address.
- Update milestone status and HTTPS design review links. Clients can approve only milestones marked for review.
- Publish available 30-minute meeting times in Johannesburg time. Slots must not overlap. Reservations are enforced atomically; cancellation returns the slot to availability. No Google Calendar sync or meeting-video link is implied.
- Publish real studio announcements and client-approved public portfolio entries. Private project records never become public automatically.

The live database intentionally contains no seeded clients, projects, testimonials, fake launches or meeting availability. Automated tests use a separate temporary database.

## Persistence and privacy

The default data directory is `.data/` inside NVTRA, ignored by Git and denied by the HTTP static-file allowlist. It contains SQLite data and private uploads. For deployment, set `NVTRA_DATA_DIR` to a persistent private volume outside the public web root. Back up the SQLite database with its backup API and the uploads directory together; do not copy a live WAL database file in isolation. Restrict the volume to the application user and define retention/deletion procedures appropriate to your business before accepting public client data.

Passwords use salted scrypt. Random session tokens are hashed before storage, expire after seven days, and are carried by HttpOnly, SameSite cookies. HTTPS origins enable Secure cookies and HSTS. Project and upload endpoints check ownership or administrator status on every request. Uploaded files are limited to PDF, PNG, JPEG and UTF-8 text; 5 MB per file and 50 MB per project. They are served only as authenticated attachments, not executable inline content. Signature checking is not malware scanning; use a scanner if your production workflow requires one.

Consent is required for enquiries. Email and private project contents are not sent to Gemini automatically. Search covers public content only. Local/session storage contains viewing preferences and unsubmitted brief choices, not authentication tokens or private project files. Avoid putting secrets in briefs.

## External services

Configuration is read from process environment variables. `.env.example` documents names; `.env` files are not loaded automatically and must never be served or committed.

### Gemini support

Set `GEMINI_API_KEY` securely on the server. Create your own key through [Google AI Studio](https://aistudio.google.com/apikey); available free quotas and billing terms are controlled by Google, not this application. The code does not contain or generate a free key. `GEMINI_MODEL` defaults to `gemini-2.5-flash` and can be changed to a model supported by your account.

Allow HTTPS to `generativelanguage.googleapis.com`. Only the visitor's current question plus public studio facts are sent. The key is never exposed to the browser. When configuration is absent or the provider fails, the interface explicitly identifies the deterministic FAQ fallback. Gemini output is plain text, never executable HTML.

### Website health checks

Allow DNS resolution for public targets and HTTPS to `www.googleapis.com`. Optionally set `PAGESPEED_API_KEY` for a Google project with PageSpeed Insights enabled; quotas apply. The backend validates the public URL, then asks Google to measure it. It never fetches arbitrary target content into the application server. Results contain the actual Lighthouse categories, metric values and measurement timestamp. A failure produces an error, not a sample score. Runs can take 65 seconds, so the reverse proxy timeout must allow that duration.

Current cloud validation: direct DNS resolution of public domains fails and the outbound proxy blocks the PageSpeed destination. The application correctly reports unavailability. Successful response parsing is verified with an explicitly labelled test fixture; a real successful live audit has not been verified here.

### Enquiry and password-reset email

Set `SMTP_HOST`, `SMTP_PORT` (default 587), `SMTP_FROM`, and, if the server requires authentication, `SMTP_USER` and `SMTP_PASSWORD`. The SMTP relay must support STARTTLS with a valid certificate. Permit outbound connectivity to that relay. Credentials must be genuine server environment secrets; an HTTP proxy placeholder cannot authenticate a raw SMTP connection.

`NVTRA_INQUIRY_EMAIL` defaults to `nvtra.official@icloud.com`. An enquiry is saved before delivery is attempted. Agency email and client-copy results are reported independently as `not_configured`, `failed`, `not_requested`, or `accepted_by_mail_server`. SMTP acceptance is not a guarantee of inbox delivery. The studio inbox retains the enquiry if email fails. Do not retry a successfully saved enquiry solely to resend email.

Password-reset links expire after 30 minutes, are single-use and invalidate all existing sessions on completion. Reset functionality requires SMTP. No real email delivery or reset email has been sent in this environment.

## HTTPS deployment

Run Waitress behind a trusted HTTPS reverse proxy, with `NVTRA_PUBLIC_URL=https://your-real-domain` and the private volume mounted. Keep the backend on a loopback/private listener. Use a single application process for the current SQLite/in-memory throttling design. Configure request size limits, a 75+ second upstream timeout for audits, and public-edge rate limiting; do not trust forwarded client IP headers from arbitrary callers. Scale to a shared rate limiter and managed database before deploying multiple app processes or replicas.

The app sets a restrictive static-file allowlist, nosniff, frame-denial and a CSP. Existing inline legacy scripts/styles still require `unsafe-inline`; moving them to external modules is a future CSP-hardening step. Use CSP-aware changes when adding external embeds.

No hosting provider or public domain was supplied, and nothing was deployed. Production email delivery, provider credentials, HTTPS cookies on the actual domain, backups, and real client operation must be verified on that deployment.

## Pricing model

Edit `config/pricing.json`, then restart the server. Prices originate from the existing NVTRA published packages: Basic R499, Standard R1,499, Deluxe R2,400, R99 listed add-ons and R99/month maintenance. No unapproved custom rates were invented.

The displayed range compares the cheapest applicable package with the next package upgrade. A single applicable package displays one starting amount. E-commerce checkout, SEO campaigns, custom CMS/integrations and advanced motion/design are flagged for separate scoping and excluded from that figure. Hosting, domains and provider fees are excluded. The server recalculates submitted configuration so browser-edited totals are not trusted.

## API overview

Public reads: `/api/config`, `/api/session`, `/api/activity`, `/api/showcase`, `/api/slots`.

Public writes with JSON and exact Origin: `/api/register`, `/api/login`, `/api/password-reset`, `/api/password-reset/confirm`, `/api/estimate`, `/api/inquiries`, `/api/assistant`, `/api/health`.

Authenticated: `/api/dashboard`, `/api/saved`, `/api/saved/delete`, `/api/bookings`, `/api/bookings/cancel`, `/api/logout`, `/api/projects/:id`, `/api/projects/:id/comments`, `/api/projects/:id/uploads`, `/api/projects/:id/approve`, `/api/uploads/:id`.

Administrator: `/api/admin` and POST `/api/admin/projects`, `/api/admin/milestones`, `/api/admin/slots`, `/api/admin/slots/delete`, `/api/admin/activity`, `/api/admin/showcase`.
