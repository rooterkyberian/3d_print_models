"""Checks exported CAD, grip depths, rope channels, and STL topology.

Usage: python verify.py [DEPTHS ...]; checks every built variant by default.
"""

import json
import math

import cadquery as cq
import numpy as np
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Dir, gp_Lin, gp_Pnt
from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
from OCP.TopAbs import TopAbs_IN, TopAbs_ON
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

from variants import built, front_height


def verify(p):
    c = json.loads((p / "parameters.json").read_text())
    W, H, ZMAX = c["dimensions_mm"]
    BACK = c["floor_z_mm"]
    PH = c["pocket_size_mm"][1]
    RX, RZ, RR = c["rope_x_mm"], c["rope_z_mm"], c["channel_radius_mm"]
    CR = c["cord_diameter_mm"] / 2
    s = cq.importers.importStep(str(p / (c["name"] + ".step"))).val()
    assert s.isValid() and len(s.Solids()) == 1
    classifier = BRepClass3d_SolidClassifier(s.wrapped)

    def inside(q, tol=1e-6):
        classifier.Perform(gp_Pnt(q.x, q.y, q.z), tol)
        return classifier.State() in (TopAbs_IN, TopAbs_ON)

    print(c["name"], "CAD loaded and valid", flush=True)
    b = Bnd_Box()
    BRepBndLib.AddOptimal_s(s.wrapped, b, False, False)
    limits = b.Get()
    dimensions = [limits[k + 3] - limits[k] for k in range(3)]
    assert np.allclose(dimensions, c["dimensions_mm"], atol=1e-5)
    intersector = IntCurvesFace_ShapeIntersector()
    intersector.Load(s.wrapped, 1e-7)
    TOP = ZMAX + 11

    def ray(x, y, z=TOP, d=(0, 0, -1), length=TOP + 5):
        i = intersector
        i.Perform(gp_Lin(gp_Pnt(x, y, z), gp_Dir(*d)), 0, length)
        hits = sorted(
            [
                (i.WParameter(k), tuple(i.Pnt(k).Coord()))
                for k in range(1, i.NbPnt() + 1)
            ]
        )
        # A ray through a shared CAD edge may hit both adjoining faces at the
        # same location. Count the physical crossing once, rather than a zero wall.
        unique = []
        for hit in hits:
            if not unique or abs(hit[0] - unique[-1][0]) > 1e-6:
                unique.append(hit)
        return unique

    depths = []
    rr = c["pocket_root_radius_mm"]
    gr = c["grip_edge_radius_mm"]
    wall = PH / 2
    spans = c["front_spans_mm"]
    for yc, lo, hi in c["pockets"]:
        for sign, target in [(-1, lo), (1, hi)]:
            # Lip probe on the level stretch past the grip edge round.
            lip = ray(20, yc + sign * (wall + gr + c["grip_flat_mm"] / 2))[0][1][2]
            # Floor probe sits 1 mm beyond the root fillet.
            floor = ray(20, yc + sign * (wall - rr - 1))[0][1][2]
            assert abs(floor - BACK) < 1e-6 and abs(lip - floor - target) < 1e-6
            # 0.5 mm from the wall, the root fillet raises the floor by R-sqrt(R^2-(R-0.5)^2).
            root = ray(20, yc + sign * (wall - 0.5))[0][1][2]
            assert (
                abs(root - (BACK + rr - math.sqrt(rr * rr - (rr - 0.5) ** 2))) < 1e-5
            ), (yc, sign, root)
            # The grip edge round lowers the front by R-sqrt(R^2-(R-u)^2) at u from the wall.
            for u in (0.3, 1.5):
                grip = ray(20, yc + sign * (wall + u))[0][1][2]
                assert (
                    abs(lip - grip - (gr - math.sqrt(gr * gr - (gr - u) ** 2))) < 1e-5
                ), (yc, sign, u, grip)
            depths.append(
                {
                    "y": yc,
                    "side": "lower" if sign < 0 else "upper",
                    "depth_mm": lip - floor,
                    "root_z_0.5mm_from_wall": root,
                    "grip_drop_1.5mm_from_wall": lip - grip,
                }
            )
        # A full-height 30 mm-clear rectangle remains empty 1 mm before the rear floor.
        for xx in [-40, 0, 40]:
            for yy in [-15, -7, 0, 7, 15]:
                assert not inside(cq.Vector(xx, yc + yy, BACK + 1), 1e-6)
    print("Grip depths, edge rounds and clearance passed", flush=True)
    # The front follows its profile, level or in S-curves without steps: at X=20
    # across the bars, clear of the pockets and grip rounds, and along the side
    # rails at X=+-56, where it also changes height beside each pocket.
    # Sample grids are offset 0.013 mm: a ray exactly along the seam between
    # two faces of a steep S can miss both.
    profile_samples = 0
    for y in np.arange(-H / 2 + 4, H / 2 - 4, 0.25) + 0.013:
        near_pocket = any(abs(y - yc) < wall + gr for yc, _, _ in c["pockets"])
        for x in ([] if near_pocket else [20]) + [-56, 56]:
            z = ray(x, y)[0][1][2]
            assert abs(z - front_height(spans, y)) < 1e-5, (x, y, z)
            profile_samples += 1
    print("Front profile passed", flush=True)
    # Labels: a grid of rays over each finds either the front or a recess floor
    # 0.6 mm below it, sloping with the front, and no recess on the grip round.
    LU = c["label_offset_mm"]
    labels = []
    for yc, lo, hi in c["pockets"]:
        for sign in (-1, 1):
            label_y = yc + sign * (wall + LU)
            recessed = 0
            for u in np.arange(gr, LU + 2.5, 0.2) + 0.013:
                y = yc + sign * (wall + u)
                f = front_height(spans, y)
                for x in np.arange(-6, 6, 0.2):
                    z = ray(x, y)[0][1][2]
                    if abs(z - (f - 0.6)) < 1e-5:
                        recessed += 1
                    else:
                        assert abs(z - f) < 1e-5, (x, y, z, f)
            assert recessed > 50, (label_y, recessed)
            labels.append({"y": label_y, "recessed_samples": recessed})
    print("Labels passed", flush=True)
    # See-through: rays parallel to each channel, within 0.2 mm of the nominal
    # bore, cross the whole board unhindered.
    see_through = 0
    for sx in [-1, 1]:
        for r in [0, (RR - 0.2) / 2, RR - 0.2]:
            for ang in np.linspace(0, 2 * math.pi, 8, endpoint=False):
                x, z = sx * RX + r * math.cos(ang), RZ + r * math.sin(ang)
                assert ray(x, -H / 2 - 5, z, (0, 1, 0), H + 10) == [], (sx, r, ang)
                see_through += 1
    print("Straight see-through channels passed", flush=True)
    # Exits: the inner side is a round of exit_radius about (cx,cy), so a rope
    # turning towards the board centre bears on it. Check material just inside
    # and air just outside that radius through the whole 90 degree turn, and
    # clearance for the cord along the trough centreline until it leaves the board.
    ER = c["exit_radius_mm"]
    TK = c["track_depth_mm"]
    CH = c["corner_chamfer_mm"]
    Rb = ER + c["exit_trough_radius_mm"]
    exits = []
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            cx, cy = (
                sx * (RX - RR - c["exit_sweep_oversize_mm"] - ER),
                sy * (H / 2 - TK - ER),
            )
            for t in np.radians([15, 30, 45, 60, 75, 85, 89]):
                u = cq.Vector(sx * math.cos(t), sy * math.sin(t), 0)
                assert inside(cq.Vector(cx, cy, RZ) + u * (ER - 0.05)) and not inside(
                    cq.Vector(cx, cy, RZ) + u * (ER + 0.05)
                ), (sx, sy, t)
            # From 3 degrees: at 0 the samples are coplanar with the sweep's start
            # face, which misleads the point classifier; see-through rays cover it.
            for t in np.radians(np.linspace(3, 45, 8)):
                u = cq.Vector(sx * math.cos(t), sy * math.sin(t), 0)
                centre = cq.Vector(cx, cy, RZ) + u * Rb
                for ang in np.linspace(0, 2 * math.pi, 8, endpoint=False):
                    assert not inside(
                        centre
                        + u * (CR * math.cos(ang))
                        + cq.Vector(0, 0, CR * math.sin(ang)),
                        1e-6,
                    ), (sx, sy, t, ang)
            # Corner cut at 45 degrees, CH from the corner, below the rope plane.
            x = abs(ray(sx * 90, sy * (H / 2 - 5), 2, (-sx, 0, 0), 45)[0][1][0])
            assert abs(x - (W / 2 - CH + 5)) < 1e-5, (sx, sy, x)
            exits.append({"side": sx, "end": sy, "chamfer_x_at_5mm_mm": x})
    # The end faces carry a TK-deep track at the rope plane between the exits,
    # and are flat beside it.
    track = []
    for sy in [-1, 1]:
        for x in (-30, 0, 30):
            depth = ray(x, sy * (H / 2 + 5), RZ, (0, -sy, 0), 10)[0][0] - 5
            assert abs(depth - TK) < 1e-6, (sy, x, depth)
            track.append({"end": sy, "x": x, "depth_mm": depth})
            assert (
                abs(ray(x, sy * (H / 2 + 5), RZ + RR + 1, (0, -sy, 0), 10)[0][0] - 5)
                < 1e-6
            )
    print("Rounded exits, rope track and corner cuts passed", flush=True)
    # Collars: closed tunnels COLLAR long at each end. Below the rope axis they
    # reach the side; above it the rope is enclosed by a tube of radius TO.
    CY = H / 2 - c["collar_length_mm"]
    SH = c["shelf_x_mm"]
    TO = c["tube_outer_radius_mm"]
    # Height above the axis where the side plane cuts the tube; tube probes sit
    # midway between it and the top of the bore.
    dz = (math.sqrt(TO * TO - (W / 2 - RX) ** 2) + RR) / 2
    collar_measurements = []
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            # Probe midway between where the exit round leaves the bore and the
            # collar's inner end, where the collar is plain bore.
            y = sy * (H / 2 - (ER + TK + c["collar_length_mm"]) / 2)
            assert (
                abs(abs(ray(sx * 90, y, RZ - 2, (-sx, 0, 0), 45)[0][1][0]) - W / 2)
                < 1e-5
            ), (sx, sy)
            hits = ray(sx * 90, y, RZ + dz, (-sx, 0, 0), 45)
            tube_x, bore_x = abs(hits[0][1][0]), abs(hits[1][1][0])
            assert (
                abs(tube_x - (RX + math.sqrt(TO * TO - dz * dz))) < 1e-5
                and abs(bore_x - (RX + math.sqrt(RR * RR - dz * dz))) < 1e-5
            ), (sx, sy, tube_x, bore_x)
            # Roofed by the tube 1 mm inside the collar, open 1 mm beyond it.
            roof = ray(sx * (RX + 1), sy * (CY + 1))[0][1][2]
            assert abs(roof - (RZ + math.sqrt(TO * TO - 1))) < 1e-5, (sx, sy, roof)
            seat = ray(sx * RX, sy * (CY - 1))[0][1][2]
            assert abs(seat - (RZ - RR)) < 1e-5, (sx, sy, seat)
            collar_measurements.append(
                {"side": sx, "end": sy, "tube_outer_x_mm": tube_x, "roof_z_mm": roof}
            )
    print("Collars passed", flush=True)
    # Between the collars: below the rope axis the board reaches the side; above
    # it, cut back to the shelf wall; the rope rests in an open half-pipe.
    # Shelf wall probes start 0.5 mm above where the bore meets the wall.
    wall0 = math.sqrt(RR * RR - (RX - SH) ** 2) + 0.5
    seat_measurements = []
    for sx in [-1, 1]:
        for yy in np.linspace(-CY + 2, CY - 2, 5):
            for zz in (2, RZ / 2, RZ - 1):
                assert (
                    abs(abs(ray(sx * 90, yy, zz, (-sx, 0, 0), 45)[0][1][0]) - W / 2)
                    < 1e-5
                ), (sx, yy, zz)
            for zz in [
                RZ + wall0 + d
                for d in (0, 3, 7)
                if RZ + wall0 + d < BACK + min(c["depths_mm"]) - 1.5
            ]:
                x = abs(ray(sx * 90, yy, zz, (-sx, 0, 0), 45)[0][1][0])
                assert abs(x - SH) < 1e-5, (sx, yy, zz, x)
            for dx in (0, 2):
                z = ray(sx * (RX + dx), yy)[0][1][2]
                assert abs(z - (RZ - math.sqrt(RR * RR - dx * dx))) < 1e-5, (
                    sx,
                    yy,
                    dx,
                    z,
                )
            seat_measurements.append(
                {"side": sx, "y": yy, "seat_bottom_z_mm": ray(sx * RX, yy)[0][1][2]}
            )
    print("Open rope seats passed", flush=True)
    raw = (p / (c["name"] + ".stl")).read_bytes()
    nt = int.from_bytes(raw[80:84], "little")
    assert len(raw) == 84 + nt * 50
    r = np.frombuffer(
        raw,
        dtype=np.dtype([("normal", "<f4", 3), ("v", "<f4", (3, 3)), ("attr", "<u2")]),
        offset=84,
    )
    vs, ids = np.unique(np.round(r["v"].reshape(-1, 3), 5), axis=0, return_inverse=True)
    faces = ids.reshape(-1, 3)
    edges = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    und, counts = np.unique(np.sort(edges, axis=1), axis=0, return_counts=True)
    assert (counts == 2).all(), (
        "nonmanifold/boundary",
        np.unique(counts, return_counts=True),
    )
    _, oriented = np.unique(edges, axis=0, return_counts=True)
    assert (oriented == 1).all()
    a, bb, cc = (
        r["v"][:, 0].astype(float),
        r["v"][:, 1].astype(float),
        r["v"][:, 2].astype(float),
    )
    areas = np.linalg.norm(np.cross(bb - a, cc - a), axis=1) / 2
    assert (areas > 1e-10).all()
    vol = np.einsum("ij,ij->i", a, np.cross(bb, cc)).sum() / 6
    assert abs(vol - s.Volume()) / s.Volume() < 0.001
    adj = coo_matrix(
        (np.ones(len(und)), (und[:, 0], und[:, 1])), shape=(len(vs), len(vs))
    )
    ncomp, _ = connected_components(adj, directed=False)
    assert ncomp == 1
    result = {
        "status": "PASS",
        "name": c["name"],
        "dimensions_mm": dimensions,
        "volume_cm3": s.Volume() / 1000,
        "depths": depths,
        "collars": collar_measurements,
        "open_seats": seat_measurements,
        "exits": exits,
        "track": track,
        "front_profile_samples": profile_samples,
        "labels": labels,
        "see_through_rays": see_through,
        "stl_triangles": nt,
        "open_edges": int(sum(counts == 1)),
        "nonmanifold_edges": int(sum(counts > 2)),
        "connected_components": int(ncomp),
        "degenerate_triangles": int(sum(areas < 1e-10)),
        "relative_mesh_volume_error": abs(vol - s.Volume()) / s.Volume(),
        "load_rating": "UNTESTED; geometry checks only",
    }
    (p / "verification.json").write_text(json.dumps(result, indent=2))
    print(c["name"], "PASS", flush=True)


for p in built():
    verify(p)
