# Reference audit and design decisions

Audited 10 November 2026. Every supplied Instagram reel was requested directly. The environment's outbound proxy rejected every request with HTTP 403. No frames were accessible, so no visual properties are claimed as observed.

| Reference | Result | Observed inventory | Inferred from footage |
| --- | --- | --- | --- |
| https://www.instagram.com/reel/DfebUgsuvgV/ | Inaccessible, proxy 403 | None | None |
| https://www.instagram.com/reel/DfbyRdUxVWT/ | Inaccessible, proxy 403 | None | None |
| https://www.instagram.com/reel/DfN2BG7RomD/ | Inaccessible, proxy 403 | None | None |
| https://www.instagram.com/reel/DfO2R6OxrPL/ | Inaccessible, proxy 403 | None | None |
| https://www.instagram.com/reel/DfJ3V1DRIYl/ | Inaccessible, proxy 403 | None | None |
| https://www.instagram.com/reel/DfFYv20JsLl/ | Inaccessible, proxy 403 | None | None |
| https://www.instagram.com/reel/Db47cnKxXPz/ | Inaccessible, proxy 403 | None | None |
| https://www.instagram.com/reel/DfFwwiWuheO/ | Inaccessible, proxy 403; highest-priority pricing reference | None | None |

Screen recordings or screenshots are needed to audit the actual layouts, typography, motion timing, pointer behavior, mobile states and pricing interactions. This implementation is not represented as an exact recreation of those reels. The inline image references in the request were not used as evidence of interactive behavior.

## Directly inspected starting point

The existing NVTRA source had gold/ivory tokens, a dark/light theme, Playfair Display and DM Sans typography, pill-shaped glass navigation, large editorial headings, a one-shot WebGL hero, service rows, pricing cards, and two identical HTML entry points. The previous iteration added a responsive contour field and initial Vision Lab. These are source observations, not observations of Instagram.

## New design and component inventory

| Component | Placement and behavior | Implementation |
| --- | --- | --- |
| Pricing ledger | Pricing page: controls on the left, live package amount and scope on the right, then expandable package comparison | Shared JSON price model; instant client calculation; authoritative server recalculation on enquiry |
| Brief studio | Dedicated Vision Lab: five revisitable steps with a persistent visual preview | Session storage, native controls, live theme/type/density/palette changes; restrained CSS motion |
| Transformation studio | Explore: complete legacy and redesigned fictional café layouts | Native keyboard-accessible range control and clipping mask; three design approaches |
| Measurement panel | Explore: public URL input, measured scores or an explicit unavailable state | Server-to-server PageSpeed request; no locally invented health score |
| Private studio | Dashboard and project routes, distinct from the public portfolio | Session-authenticated API, per-project access control, milestones, content and feedback |
| Studio journal | About and News | Administrator-published events only; honest empty state |
| Portfolio catalogue | Work; category controls, project summaries and real external links | Explicit public records separate from private projects; no fabricated clients or testimonials |
| Search and support | Native dialogs available from every route | Immediate local content search; server-side FAQ/Gemini support |
| Viewing preferences | Appearance dialog | Locally persisted theme, accent, density, text size, contrast, motion |
| Quiet corner | Type `nvtra` outside text fields or double-click the brand | Nonessential accessible dialog; no flashing, no tracking |

The existing framework-free frontend is retained rather than introducing a full framework migration alongside private data features. Python owns the API and SQLite persistence. Waitress supplies the production WSGI listener. Runtime dependencies stay small; animation is confined to purposeful components and respects reduced motion.
