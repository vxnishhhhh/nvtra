# Vercel frontend deployment

The original root HTML expects the persistent Python API at `/api/config`. Serving that HTML as a static Vercel deployment leaves those endpoints missing and produces “The studio is temporarily unavailable.” The repository now explicitly builds the self-contained frontend for Vercel instead.

`vercel.json` selects no framework, runs `node scripts/build_vercel.cjs`, and serves `dist-vercel`. That build copies only the tested standalone frontend and robots file. It makes no API calls, exposes no Python/server/private files, needs no packages or secrets, and does not try to run SQLite on ephemeral function storage. Vercel can display the design, pricing calculator, Vision Lab, search, simulator, FAQ and enquiry downloads/email preparation now. It clearly identifies this as a preview; secure accounts, private projects and reservations remain unavailable until the persistent backend is connected.

For the existing `nvtra-xxxx.vercel.app` project:

1. Confirm the connected repository is `vxnishhhhh/nvtra`, the production branch is `main`, and the Root Directory is the repository root.
2. Let the latest Git push create a deployment. If automatic deployment is disabled, deploy the latest `main` commit. Redeploying an older deployment can reuse its older source; confirm the commit in the deployment details.
3. Use the repository's settings. If manually overriding them in Vercel, select **Other** framework, Build Command `node scripts/build_vercel.cjs`, Output Directory `dist-vercel`, and Install Command `node --version`.
4. Open the production URL after the new deployment succeeds. Pricing and Vision Lab should render without an unavailable-server message; the interactive-preview notice confirms the correct build is served.

Build and browser-check locally with `node tests/vercel.cjs` (Playwright and Chromium required; set `CHROMIUM_PATH` when using system Chromium). The check runs the real build, verifies only public output is included, then exercises the output with all external network requests blocked and checks that it sends zero API requests.

The full no-subscription backend setup is in [FREE-HOSTING.md](FREE-HOSTING.md). Once the free PythonAnywhere website is running, its actual HTTPS address is needed to connect the full site. Do not replace persistent storage with `/tmp` on Vercel or expose credentials in frontend variables.

The local build and browser interactions were verified here. The workspace's outbound proxy blocks the production URL, and no Vercel account/API access is connected, so a successful live deployment has not been verified from this environment.
