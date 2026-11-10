# NVTRA without subscriptions

The paid Render setup has been removed. NVTRA's Python/SQLite backend has no paid library, database, authentication, booking, storage-service or application subscription. The hosted route below uses a **PythonAnywhere Beginner/free account**, its included disk, and its free HTTPS subdomain. Do not select a paid plan, buy a domain, add billing to Google, or purchase quota to use this setup.

## See the frontend now

Download [preview.html](../preview.html) using GitHub's **Download raw file** button and open it in a browser. It is a standalone HTML file containing the styles, scripts and public configuration. No server, login or installation is needed. Optional web fonts fall back to local fonts if offline.

The preview supports the 3D hero, exhibition, studies, process scene, pricing, Vision Lab, brief downloads, redesign comparison, playground, search, themes, accessibility preferences, FAQ guidance and Easter egg. Enquiries can be downloaded and opened in your own email app. It does not pretend to create private accounts, submit enquiries, reserve meetings or publish live client data. Sign-in is explicitly disabled until a backend is connected. The health-check control opens Google's real free PageSpeed tool; it does not generate fake measurements.

Optional online preview: in GitHub **Settings → Pages**, choose **GitHub Actions** as the source. In **Actions → Publish free design preview**, choose **Run workflow**. This publishes only the public HTML preview; it never uploads the Python source, database, credentials or private files. GitHub Pages is free for public repositories. This workflow is manual, and does not publish private records. The URL is reported by the successful deployment, not assumed in advance.

## Deploy the complete backend for free

1. Create a **Beginner/free** account at [PythonAnywhere](https://www.pythonanywhere.com/). Keep the free plan. Send only the username or free domain if you want help tailoring the commands; never send a password or API key in chat.
2. Open a Bash console in that account and clone the public repository:

   ```sh
   git clone https://github.com/vxnishhhhh/nvtra.git
   cd nvtra
   ```

3. In the **Web** tab, add a web app on the included free domain, select **Manual configuration**, and select Python 3.12 or a newer supported version. The application is WSGI and standard-library Python; no virtual environment or pip installation is needed for this host.
4. Back in the console, use the exact domain from the Web tab:

   ```sh
   python3 scripts/setup_free_host.py --domain YOUR-USERNAME.pythonanywhere.com
   ```

   EU accounts may use `YOUR-USERNAME.eu.pythonanywhere.com`; use the actual domain shown by the host. The generator rejects unrelated domains and refuses to overwrite an existing generated file. It creates `~/nvtra_wsgi.py` with public configuration only. Copy that file's contents into the WSGI configuration file linked from the Web tab. Do not map the repository or private data directory as static files: the application serves an explicit allowlist of public assets.
5. Click **Reload** in the Web tab. Open the HTTPS domain shown there. Both the frontend and backend are served together, so authentication and forms use the same secure origin.
6. Create your administrator in the Bash console using the same private storage location:

   ```sh
   cd ~/nvtra
   NVTRA_DATA_DIR="$HOME/.local/share/nvtra" python3 server.py --create-admin nvtra.official@icloud.com
   ```

   Enter your password only in that private terminal prompt. Sign into the website and use **My studio → Studio operations** to manage enquiries, accepted projects, milestones, announcements and availability.

Private SQLite data and uploaded files are kept in `~/.local/share/nvtra`, outside the repository. They persist between web-app reloads. Back up them together using the SQLite backup API and protected copies of the uploads; don't publish them or commit them.

## What free means here

PythonAnywhere's official free-account documentation lists **one web app/worker, 512 MiB total disk, and a one-month web-app expiry**. Renew the web app in its Web tab before expiry; this is an account action, not a paid subscription. Console CPU limits also apply; their documentation says those CPU-second limits do not apply to web apps. There is no paid scaling or automatic upgrade configured by NVTRA. If a quota is exhausted, stay within the free limits or pause the affected feature; do not enable billing. Keep local virtual environments and test datasets off this small hosting account.

The limits were checked against PythonAnywhere's [official help source](https://github.com/pythonanywhere/help_pages/blob/3872b734cfb44d5df1082d9afbe054dd53884f70/articles/FreeAccountsFeatures.md), including its 2026 free-account changes. Hosting terms can change; confirm the free plan at signup. No unlimited or permanent third-party free capacity is promised.

| Feature | Free implementation / requirement |
| --- | --- |
| Accounts, passwords, private dashboard | Existing Python backend and SQLite; no paid auth vendor |
| Projects, comments, approvals and uploads | Included host filesystem; within the account's disk quota |
| Estimator, submitted briefs, stored enquiries | Existing server validation and database; no form-service subscription |
| Real booking calendar | Administrator-published slots and transactional reservations; no paid calendar service |
| Search, simulator, timeline, real feed, themes, accessibility, Easter eggs | Browser code and administrator-published records |
| Support | FAQ guidance works without any key. Gemini is optional, with a key from a Google project **without billing enabled**, and only while its free quota/model is available. On failure the labelled FAQ fallback remains available. |
| Website health check | Google's PageSpeed/Lighthouse API, subject to its free quota and host network permissions. The external PageSpeed tool is a free fallback; no fabricated results. |
| Enquiry email / reset email | Optional existing free mailbox SMTP, subject to that provider's policies and PythonAnywhere network access. No paid email API is required. Without SMTP, enquiries stay in the administrator inbox; email reset remains unavailable. |

Free PythonAnywhere accounts use an outbound allowlist. Verify `generativelanguage.googleapis.com`, `www.googleapis.com`, and the chosen mail relay on the actual account. If a destination is blocked, request an allowlist addition through their free support process or use the documented local/browser fallback; do not upgrade to a paid plan. Gemini availability, SMTP delivery, and live audits have not been verified on the new account yet. Configure optional secrets only in private host configuration injected into the WSGI process, never in the repository or frontend.

## Update the deployed site

Run `git pull --ff-only` in `~/nvtra`, then click **Reload** in the Web tab. This does not remove the separate private database/uploads. Keep the existing WSGI origin and storage path. Verify a controlled login, enquiry and reservation on the deployed HTTPS URL before accepting real clients.
