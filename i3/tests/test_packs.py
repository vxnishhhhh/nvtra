"""Every page of every shipped content pack must build, and the app must serve it.

    python -m pytest tests      or      python tests/test_packs.py
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from i3 import create_app, load, validate  # noqa: E402
from i3 import pages  # noqa: E402
from i3.content import rich  # noqa: E402

PACKS = sorted((ROOT / "content").glob("*.json"))


def test_every_page_builds():
    assert PACKS, "no content packs found"
    for pack in PACKS:
        content = load(pack)
        for page in content["pages"]:
            assert pages.build(page, content) is not None, f"{pack.name} {page['path']}"


def test_app_serves_shell_and_assets():
    for pack in PACKS:
        client = create_app(load(pack)).server.test_client()
        assert client.get("/").status_code == 200
        for asset in ("i3.css", "i3.js", "land.json"):
            assert client.get(f"/assets/{asset}").status_code == 200, asset


def test_state_and_ask_endpoints():
    app = create_app(load(PACKS[0]), state_provider=lambda: {"score": "1"},
                     ask_handler=lambda q, path: f"echo {q}")
    client = app.server.test_client()
    assert client.get("/i3/state").get_json() == {"score": "1"}
    assert client.post("/i3/ask", json={"question": "hi"}).get_json() == {"answer": "echo hi"}


def test_validation_names_the_problem():
    for bad, needle in [({"pages": []}, "brand"),
                        ({"brand": {}, "pages": [{"path": "/", "type": "nope"}]}, "type"),
                        ({"brand": {}, "pages": [{"path": "/x", "type": "home"}]}, "'/'")]:
        try:
            validate(bad)
        except ValueError as error:
            assert needle in str(error)
        else:
            raise AssertionError(f"accepted {bad}")


def test_highlight_markup():
    parts = rich("a [[b]] c")
    assert parts[0] == "a " and parts[1].children == "b" and parts[2] == " c"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
