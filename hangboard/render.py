"""Orthographic depth-buffer renderer for the exported STL. Label recess floors
are shown darker for legibility; this is display coloring, not multiple materials.

Usage: python render.py [DEPTHS ...]; renders every built variant by default.
"""

import json

import numpy as np
from PIL import Image

from variants import built, front_height

VIEWS = [
    ("preview.png", [110, 190, 310]),
    ("front.png", [0, 0, 400]),
    ("rope-exits.png", [130, 260, 100]),
    ("side.png", [340, 65, 160]),
    ("bottom.png", [0, -1, 0]),
]


def render(p):
    c = json.loads((p / "parameters.json").read_text())
    raw = (p / (c["name"] + ".stl")).read_bytes()
    r = np.frombuffer(
        raw,
        dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]),
        offset=84,
    )
    t = r["v"].astype(float)
    n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    n /= np.linalg.norm(n, axis=1)[:, None]
    light = np.array([-0.5, -0.65, 1.0])
    light /= np.linalg.norm(light)
    sh = 0.35 + 0.65 * np.maximum(0, n @ light)
    colors = sh[:, None] * np.array([238, 166, 56])[None, :]
    # Label recess floors: upward faces at each label, 0.6 mm below the front.
    label = np.zeros(len(t), dtype=bool)
    centre = t.mean(axis=1)
    PH = c["pocket_size_mm"][1]
    LU = c["label_offset_mm"]
    for yc, _, _ in c["pockets"]:
        for ly in (yc - PH / 2 - LU, yc + PH / 2 + LU):
            for i in np.where(
                (abs(centre[:, 0]) < 6)
                & (abs(centre[:, 1] - ly) < 2.6)
                & (n[:, 2] > 0.3)
            )[0]:
                label[i] = (
                    centre[i, 2] < front_height(c["front_spans_mm"], centre[i, 1]) - 0.3
                )
    colors[label] *= 0.35
    for name, cam in VIEWS:
        c_ = np.array(cam, dtype=float)
        c_ /= np.linalg.norm(c_)
        # Views along Y (the rope channels) need another up reference.
        right = np.cross([0, 1, 0] if abs(c_[1]) < 0.99 else [0, 0, 1], c_)
        right /= np.linalg.norm(right)
        up = np.cross(c_, right)
        coords = t - np.array([0, 0, c["dimensions_mm"][2] / 2])
        pts = np.stack([coords @ right, coords @ up, coords @ c_], axis=-1)
        size = 1400
        scale = (size - 120) / max(np.ptp(pts[:, :, 0]), np.ptp(pts[:, :, 1]))
        pts[:, :, 0] = pts[:, :, 0] * scale + size / 2
        pts[:, :, 1] = -pts[:, :, 1] * scale + size / 2
        zbuffer = np.full((size, size), -np.inf)
        canvas = np.full((size, size, 3), 248, dtype=np.uint8)
        for i in np.where(n @ c_ > 1e-7)[0]:
            q = pts[i]
            xmin = max(0, int(np.floor(q[:, 0].min())))
            xmax = min(size - 1, int(np.ceil(q[:, 0].max())))
            ymin = max(0, int(np.floor(q[:, 1].min())))
            ymax = min(size - 1, int(np.ceil(q[:, 1].max())))
            if xmax < xmin or ymax < ymin:
                continue
            x, y = np.meshgrid(
                np.arange(xmin, xmax + 1) + 0.5, np.arange(ymin, ymax + 1) + 0.5
            )
            den = (q[1, 1] - q[2, 1]) * (q[0, 0] - q[2, 0]) + (q[2, 0] - q[1, 0]) * (
                q[0, 1] - q[2, 1]
            )
            if abs(den) < 1e-10:
                continue
            u = (
                (q[1, 1] - q[2, 1]) * (x - q[2, 0])
                + (q[2, 0] - q[1, 0]) * (y - q[2, 1])
            ) / den
            v = (
                (q[2, 1] - q[0, 1]) * (x - q[2, 0])
                + (q[0, 0] - q[2, 0]) * (y - q[2, 1])
            ) / den
            w = 1 - u - v
            z = u * q[0, 2] + v * q[1, 2] + w * q[2, 2]
            zb = zbuffer[ymin : ymax + 1, xmin : xmax + 1]
            mask = (u >= -1e-8) & (v >= -1e-8) & (w >= -1e-8) & (z > zb)
            zb[mask] = z[mask]
            canvas[ymin : ymax + 1, xmin : xmax + 1][mask] = colors[i].astype(np.uint8)
        # Crop to the model plus a margin, so flat views such as the bottom are not mostly empty.
        rows, cols = np.where((canvas != 248).any(axis=2))
        y0, y1 = max(0, rows.min() - 60), min(size, rows.max() + 61)
        x0, x1 = max(0, cols.min() - 60), min(size, cols.max() + 61)
        img = Image.fromarray(canvas[y0:y1, x0:x1])
        img.resize(
            (round(img.width * 1000 / size), round(img.height * 1000 / size)),
            Image.Resampling.LANCZOS,
        ).save(p / name)
        print("Rendered", p.name, name, flush=True)


for p in built():
    render(p)
print("Rendered STL with depth buffer")
