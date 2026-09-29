"""Model registry and downloader for Qualcomm AI Hub assets.

Every model PunarGati runs comes from Qualcomm AI Hub's public release bucket
(the same URLs listed in each ``huggingface.co/qualcomm/<model>/release_assets.json``).
Downloads are pinned to a release and verified with SHA-256, so a model can't
silently change underneath a clinical measurement.

    python -m punargati.models            # show status
    python -m punargati.models download   # fetch anything missing
"""

from __future__ import annotations

import hashlib
import io
import json
import shutil
import sys
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = REPO_ROOT / "models"
AIHUB = "https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models"


@dataclass(frozen=True)
class ModelAsset:
    key: str            # local folder name under models/
    model_id: str       # AI Hub model id
    precision: str
    url: str
    sha256: str         # of the zip
    onnx_file: str
    license: str
    source: str         # human-readable provenance

    @property
    def dir(self) -> Path:
        return MODELS_DIR / self.key

    @property
    def onnx_path(self) -> Path:
        return self.dir / self.onnx_file

    def present(self) -> bool:
        return self.onnx_path.is_file()

    def metadata(self) -> dict:
        p = self.dir / "metadata.json"
        return json.loads(p.read_text()) if p.is_file() else {}


ASSETS: dict[str, ModelAsset] = {
    # MoveNet (Lightning) single-person pose — the always-on tracker. Quantized
    # w8a16 is the NPU build (all 214 ops on HTP per AI Hub's X Elite profile).
    "movenet-w8a16": ModelAsset(
        key="movenet-w8a16", model_id="movenet", precision="w8a16_mixed_int16",
        url=f"{AIHUB}/movenet/releases/v0.63.0/movenet-onnx-w8a16_mixed_int16.zip",
        sha256="f66a58ebb11d4ea16d4f9559c302947b8aaf35442a002ef60c4b9537644a1527",
        onnx_file="movenet.onnx", license="Apache-2.0",
        source="Qualcomm AI Hub · Movenet v0.63.0 · ONNX w8a16",
    ),
    # Float build: used on the Adreno GPU (QNN GPU backend) and on plain CPUs.
    "movenet-float": ModelAsset(
        key="movenet-float", model_id="movenet", precision="float",
        url=f"{AIHUB}/movenet/releases/v0.63.0/movenet-onnx-float.zip",
        sha256="2d26d8b2dc2789bcc3fbd45bb426fe837870ea33a93481350cbe14c98740df38",
        onnx_file="movenet.onnx", license="Apache-2.0",
        source="Qualcomm AI Hub · Movenet v0.63.0 · ONNX float",
    ),
    # RTMPose-Body2d (COCO-WholeBody, 133 keypoints incl. feet and hands) — "precision
    # mode": cascaded after MoveNet, which supplies the person box. Downloaded by setup
    # (not vendored: ~70 MB of weights each).
    "rtmpose-w8a16": ModelAsset(
        key="rtmpose-w8a16", model_id="rtmpose_body2d", precision="w8a16",
        url=f"{AIHUB}/rtmpose_body2d/releases/v0.63.0/rtmpose_body2d-onnx-w8a16.zip",
        sha256="a8f7723d37768b2425e83e6b0dbd5e1125d8f17bd43f3c5a315c12bab0b6b67c",
        onnx_file="rtmpose_body2d.onnx", license="Apache-2.0",
        source="Qualcomm AI Hub · RTMPose-Body2d v0.63.0 · ONNX w8a16",
    ),
    "rtmpose-float": ModelAsset(
        key="rtmpose-float", model_id="rtmpose_body2d", precision="float",
        url=f"{AIHUB}/rtmpose_body2d/releases/v0.63.0/rtmpose_body2d-onnx-float.zip",
        sha256="89b3f876ead25721c26edd5135114a92a8f9a83ef3f4deef7ecf370d10d7ff26",
        onnx_file="rtmpose_body2d.onnx", license="Apache-2.0",
        source="Qualcomm AI Hub · RTMPose-Body2d v0.63.0 · ONNX float",
    ),
}

# Which build each compute target prefers. HTP is fastest on integer graphs;
# the QNN GPU backend and the CPU EP want float.
PREFERRED = {"npu": "movenet-w8a16", "gpu": "movenet-float", "cpu": "movenet-float"}
PREFERRED_WHOLEBODY = {"npu": "rtmpose-w8a16", "gpu": "rtmpose-float", "cpu": "rtmpose-float"}


def download(asset: ModelAsset, force: bool = False) -> Path:
    if asset.present() and not force:
        return asset.onnx_path
    print(f"[models] downloading {asset.source}\n         {asset.url}")
    req = urllib.request.Request(asset.url, headers={"User-Agent": "PunarGati/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        blob = r.read()
    digest = hashlib.sha256(blob).hexdigest()
    if digest != asset.sha256:
        raise RuntimeError(
            f"checksum mismatch for {asset.key}: got {digest}, expected {asset.sha256}. "
            "Refusing to install an unverified model."
        )
    tmp = asset.dir.with_suffix(".tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            name = Path(info.filename).name  # zips nest one folder deep; flatten
            (tmp / name).write_bytes(z.read(info))
    shutil.rmtree(asset.dir, ignore_errors=True)
    tmp.rename(asset.dir)
    print(f"[models] ok  {asset.onnx_path.relative_to(REPO_ROOT)}")
    return asset.onnx_path


def ensure_all() -> None:
    for a in ASSETS.values():
        download(a)


def status() -> list[dict]:
    return [
        {"key": a.key, "precision": a.precision, "present": a.present(),
         "license": a.license, "source": a.source}
        for a in ASSETS.values()
    ]


def main(argv: list[str]) -> int:
    if argv and argv[0] == "download":
        ensure_all()
    for s in status():
        mark = "ok " if s["present"] else "-- "
        print(f"{mark} {s['key']:<16} {s['precision']:<20} {s['source']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
