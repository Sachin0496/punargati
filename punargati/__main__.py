"""python -m punargati [--target npu|gpu|cpu] [--port 8765] [--no-browser]"""

import argparse
import logging

from .server import serve


def main() -> None:
    ap = argparse.ArgumentParser(prog="punargati", description="On-device AI rehab coach for Snapdragon PCs")
    ap.add_argument("--target", default="npu", choices=["npu", "gpu", "cpu"],
                    help="compute unit for pose (falls back npu -> gpu -> cpu)")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO if a.verbose else logging.WARNING, format="%(name)s: %(message)s")
    serve(a.host, a.port, a.target, not a.no_browser)


if __name__ == "__main__":
    main()
