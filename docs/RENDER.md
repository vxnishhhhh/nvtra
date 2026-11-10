# Deploy NVTRA on Render

[Open the Render deployment](https://render.com/deploy?repo=https://github.com/vxnishhhhh/nvtra)

1. Sign into Render and connect the `vxnishhhhh/nvtra` repository. Create a Blueprint from `main` using `render.yaml` if the link does not open it directly.
2. Review the **paid Starter service and 1 GB persistent disk**. Render displays current charges before creation. The free tier cannot retain this SQLite database and private uploads across redeployments, so it is not configured here.
3. Create the service. Once its deploy succeeds, open the **actual service URL shown in Render**. No particular hostname is guaranteed. The startup script reads Render's `RENDER_EXTERNAL_URL` and `PORT` automatically; private data stays at `/var/data/nvtra`.
4. In the service's Render Shell, run `python server.py --create-admin nvtra.official@icloud.com` and enter a unique password at the private prompt. Then sign into the site and open **My studio → Studio operations**. No administrator password is committed or preselected.
5. For a custom domain, first attach it in Render and enable HTTPS, then set `NVTRA_PUBLIC_URL` to that exact origin (for example `https://your-domain.example`) and redeploy. Use the configured origin when signing in or submitting forms.

The Blueprint disables automatic deploys: later GitHub pushes are uploaded source changes, not unreviewed live releases. Use **Manual Deploy → Deploy latest commit** when ready. Keep one service instance for the current SQLite storage and in-memory rate limits. Configure backups for both the database and private uploads; see [operations](OPERATIONS.md).

Accounts, enquiries, saved briefs, estimates, the private portal and published meeting slots work without external API credentials. Add real `GEMINI_API_KEY`, optional `PAGESPEED_API_KEY`, and SMTP variables in Render's secret environment settings when desired. Never enter secrets into source files or chat. Until configured, support uses its labelled FAQ fallback; enquiries remain stored even when email is unavailable. Live audits still depend on Google and outbound network access.

After deployment, check the homepage and `/api/config`, register a controlled account, save a brief, and confirm it persists after a manual restart before accepting client work. Verify email delivery separately. This workspace verified the startup command locally; it has not created or verified a Render service.
