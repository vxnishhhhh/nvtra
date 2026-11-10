# NVTRA workspace rules

- Work in this repository. `/workspace/mtdi-studio-` is read-only: do not edit its code, dependencies, generated files or runtime state.
- Preserve the existing editorial brand. `index.html` and `nvtra.html` must remain identical.
- Read `docs/OPERATIONS.md` before changing auth, persistence, uploads, pricing, email or provider integrations.
- Public activity, projects and meeting availability must come from actual administrator-created records. Never seed invented production activity or testimonials.
- Keep credentials in the process environment only. Do not commit secrets, private uploads or `.data/`.
- Maintain ownership checks for every private project/file operation. Recalculate enquiry estimates on the server using `config/pricing.json`.
- Report saved enquiries, SMTP acceptance, actual delivery and unavailable external providers as distinct states. Never fabricate health scores or imply FAQ fallback is a live AI answer.
- Use the existing checkout; do not create worktrees unless requested.
- Run meaningful validation for the areas changed. Backend: `python -m unittest discover -s tests -p 'test_*.py' -v`. Full browser flow: `NVTRA_TEST_WSGI=1 node tests/platform.cjs` with Playwright/Chromium installed. The browser flow uses its own temporary database; do not test with invented records in the real studio database.
