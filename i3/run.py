#!/usr/bin/env python3
"""Run an I³ interface from a content pack.

    python run.py                                   placeholder pack
    python run.py --content content/inductra.json   another pack
    python run.py --port 8060 --demo-state          animate bound values with fake data
"""
import argparse
import math
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from i3 import create_app, load  # noqa: E402


def demo_state():
    """Clearly fake values so the live-binding path can be seen working."""
    t = time.time()
    score = 82 + 6 * math.sin(t / 7)
    return {
        "score": {"value": f"{score:.1f} %", "state": "ok" if score > 80 else "warn"},
        "link": {"value": "DEMO", "state": "ok"},
        "channel": {"value": f"{40 + 10 * math.sin(t / 3):.0f}", "state": "warn"},
        "module_value": f"{1.2 + 0.3 * math.sin(t / 2):.2f}",
        "module_secondary": f"{-58 + 4 * math.sin(t / 5):+.0f}",
        "age": f"{(t % 2):.1f} s",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="I³ interface framework")
    parser.add_argument("--content", default=str(ROOT / "content" / "placeholder.json"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8050)
    parser.add_argument("--demo-state", action="store_true", help="feed bound values with fake data")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args(argv)
    app = create_app(load(args.content), state_provider=demo_state if args.demo_state else None)
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
