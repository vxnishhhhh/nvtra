# I³ — Interface Framework

**Induction · Interference · Intelligence.**

I³ is the front end of Inductra Vaion, extracted so it can carry other products. It covers
the startup intro, the glass header, the scroll-locked page openings, the orbiting module
cards round the globe, the pillar orbit that opens to full screen, the document pages and
the NVTRA dock. A product writes a **content pack** (one JSON file). I³ supplies the
interface.

```
Inductra Vaion  ─┐
MTDI Studio     ─┼─ content pack ──▶  I³  ──▶  interface
AstroTech       ─┘
```

## Run it

```bash
pip install -r requirements.txt
python run.py                                  # placeholder pack, http://127.0.0.1:8050
python run.py --demo-state                     # same, with fake live values ticking
python run.py --content content/inductra.json  # Inductra Vaion rebuilt on I³
python tests/test_packs.py                     # every page of every pack builds
```

## What is in it

| Piece | Where it came from in Inductra | Driven by |
|---|---|---|
| Startup intro (WebGL shader, split title, overview card) | `theme.startup_intro`, `browser.bootStartupIntro` | `intro` |
| Glass header, nav, status pills | `webapp.app.layout`, `theme` header CSS | `brand`, `status`, page `label` |
| Page shader (flowing field lines) | `browser.bootPageShader` | automatic |
| Scroll-locked opening: magnetosphere | `ui.fieldPainter` | page `opening.kind = "field"` |
| Scroll-locked opening: signal path | `ui.mtdiFlowPainter` (now data-driven) | page `opening.kind = "flow"` + `nodes`/`links` |
| Hero (boxed title, tag, highlighted text, spec strip) | `pages.home_page` hero | page `hero` |
| Module orbit round the globe | `browser.armHomeOrbit`, `bootHomeGlobe` | `type: home` → `modules` |
| Pillar orbit, full-screen pillars | `browser.armMtdiOrbit`, `pages.mtdi_page` | `type: framework` → `pillars` |
| Numbered document page | Sixth Sense layout | `type: document` → `sections` |
| NVTRA dock | `ui` `#iv-orb` island, `browser.bootMascot` | `dock` |
| Settings (animation switch) | `pages.settings_page` | `type: settings` |

**Left behind on purpose:** sensor callbacks, Plotly figures, the MTDI scoring maths,
hand vision (camera and MediaPipe), the Spline robot and voice. Those belong to the
products. I³ gives them a place to sit (`slot` blocks, live bindings, the `ask` hook).

## Content packs

`content/placeholder.json` uses every field once and doubles as the reference.
`content/inductra.json` is a real product expressed the same way.

Page types: `home`, `framework`, `document`, `module`, `settings`.

Block kinds, usable inside any page, pillar or section:

| kind | fields |
|---|---|
| `section` | `kicker`, `title`, `copy` (string or list), `accent`, nested `blocks` |
| `text` | `copy` |
| `cards` | `cols`, `items: [{num, title, desc, href, accent}]` |
| `metrics` | `items: [{label, value, note, bind, accent}]` |
| `slot` | `label`, `note`, `height`, `id`: a reserved region for a product's own live component |
| `list` | `items` |
| `quote` | `text` |

Write `[[term]]` in any text to render it as a highlighted technical term.

## Live data and NVTRA

```python
from i3 import create_app, load

def state():                          # polled by the browser every 1.5 s
    return {"score": {"value": "84.7 %", "state": "ok"}, "channel": "42"}

def ask(question, path):              # the NVTRA dock posts here
    return my_nvtra.answer(question, context=path)

app = create_app(load("content/my_product.json"), state_provider=state, ask_handler=ask)
app.run(port=8050)
```

Any element whose content declares `"bind": "score"` follows that key. States are
`ok`, `warn`, `high` and `off`, and they colour the dot beside the value.

The browser runtime (`i3/assets/i3.js`) has no Dash dependency. It reads `data-i3-*`
attributes and `window.I3_CONFIG`, so the same CSS and JS can serve a static page or a
future React/Next.js build without changes.

## Layout

```
i3/
  i3/__init__.py       create_app, load
  i3/app.py            Dash app, routing, /i3/state and /i3/ask
  i3/pages.py          one builder per page type
  i3/components.py     header, intro, dock, hero, orbits, content blocks
  i3/content.py        pack loading, validation, [[highlight]] markup
  i3/assets/i3.css     the design system (tokens on :root)
  i3/assets/i3.js      the browser runtime
  i3/assets/land.json  Natural Earth land polygons for the globe (public domain)
  content/             content packs
  tests/               pack tests
  run.py               runner
```
