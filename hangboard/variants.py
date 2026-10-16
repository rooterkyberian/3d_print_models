"""Depth lists such as 24,22,20,18,16,14, their output directories, and the
front profile shared by the scripts."""

import math
import sys
from pathlib import Path

here = Path(__file__).parent
DEFAULT = "24,22,20,18,16,14"


def parse(spec):
    return [float(d) for d in spec.replace("-", ",").split(",")]


def dirname(depths):
    return "-".join(f"{d:g}" for d in depths)


def front_height(spans, y):
    """Front Z at Y, from the [y0,y1,z0,z1] spans of parameters.json: level
    where z0==z1, else an S of two equal arcs, level at both ends."""
    for y0, y1, z0, z1 in spans:
        if y0 - 1e-9 <= y <= y1 + 1e-9:
            if z0 == z1:
                return z0
            L, h = y1 - y0, z1 - z0
            r = (L * L + h * h) / (4 * abs(h))
            s = math.copysign(1, h)
            if y <= (y0 + y1) / 2:
                return z0 + s * (r - math.sqrt(r * r - (y - y0) ** 2))
            return z1 - s * (r - math.sqrt(r * r - (y1 - y) ** 2))
    raise ValueError(y)


def built(args=None):
    """Output directories for the given depth lists, or every built variant."""
    args = sys.argv[1:] if args is None else args
    return [here / dirname(parse(a)) for a in args] or sorted(
        x.parent for x in here.glob("*/parameters.json")
    )
