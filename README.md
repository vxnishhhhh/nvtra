# NVTRA

NVTRA is a Durban-based web design and development studio founded by Vaishnav Singh. This application combines the existing editorial studio website with an interactive pricing and client-services platform.

## Run

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/waitress-serve --listen=127.0.0.1:8080 --threads=8 --max-request-body-size=7340032 app:application
```

See [operations and deployment](docs/OPERATIONS.md) for administrator setup, private storage, credentials, email, health checks and HTTPS deployment. MTDI Studio is read-only; all changes and runtime files belong in NVTRA.

## Features

- Cinematic 3D hero, scroll-driven exhibition, explorable studio studies and five-stage process scene, with mobile and reduced-motion fallbacks.

- Live website estimator with a configurable pricing model, budget guidance, comparison, saved scopes and server-recalculated enquiries.
- Five-step Vision Lab with live previews, session persistence, brief download and contact handoff.
- Minimal, premium and bold redesign simulator with a keyboard-accessible comparison slider.
- Real PageSpeed/Lighthouse integration with measured results or explicit unavailable states.
- Registration, login, password reset and a personal dashboard for saved directions, enquiries, meetings and activity.
- Private projects with milestones, design review links, approvals, content uploads and feedback.
- Administrator controls for project assignment, published availability, real studio announcements and approved public portfolio entries.
- Real meeting reservations, separate labelled feature demos, instant search, viewing preferences, accessibility controls and a small Easter egg.
- Gemini support when a server key is configured, with an explicit FAQ fallback otherwise.

External AI, live audits and email need the configuration described in the operations guide. No credentials, client projects, fake testimonials, availability or announcements are seeded. The complete client portal is tested against temporary accounts and data.

## Code map

`index.html` and `nvtra.html` remain identical entry points. `studio.css/js` preserve the original interactive layer; `platform.css/js` contain the shared application components; `cinematic.css/js` implement the spatial design without external animation libraries. `server.py` owns persistence, validation and the API; `app.py` exposes it through WSGI. `config/pricing.json` and `config/content.json` contain public pricing and editorial content.

[Reference audit](docs/REFERENCE-AUDIT.md) records which supplied videos were inaccessible and distinguishes source observations from newly designed components. No exact Instagram recreation is claimed.

## Verify

```sh
python -m unittest discover -s tests -p 'test_*.py' -v
npm install --no-save --package-lock=false playwright
npx playwright install chromium
node tests/platform.cjs
NVTRA_TEST_WSGI=1 node tests/platform.cjs
```

The platform test starts its own isolated server and temporary database, exercises both visitor and client workflows, and removes its data afterward. Set `CHROMIUM_PATH` to an installed Chromium executable if needed. Use `node tests/smoke.cjs` against an already running instance for the original UI regression checks; `NVTRA_URL` overrides its default origin. It validates forms without submitting a live enquiry.

The backend suite covers session invalidation, cross-origin rejection, private-data isolation, upload controls, booking races, price recalculation, honest email/AI/audit states, one-time password-reset tokens, administrator publishing and rate limits. External-provider success responses in unit tests are mocked; they do not establish live provider availability.

Run `node tests/cinematic.cjs` against a running instance to check the WebGL/fallback renderer, gallery, studies, responsive scenes and expanded live brief controls.
