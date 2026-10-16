"""Portable stepped-lip hangboard, mm. Concept geometry, no rated load.

Usage: python build.py [--cord MM] [DEPTHS ...], e.g. python build.py 20,15 25,20,17,14
Each DEPTHS lists edge depths bottom to top, in pairs per pocket: the lower
edge (used upright), then the upper edge (used after a half turn). Output goes
to a directory named after the depths. Default: 24,22,20,18,16,14.
--cord is the rope diameter the channels are sized for, default 8 mm.
"""

import argparse
import itertools
import json
import math

import cadquery as cq
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet

from clean_stl import clean
from variants import DEFAULT, dirname, here, parse

# Floor under the pockets. FEA of a 10 mm floor found it lightly loaded (about
# a tenth of PLA's in-layer strength at 100 kg); its bending stress scales
# with 1/thickness^2, so 7 mm roughly doubles that.
BACK = 7.0
PW, PH = 100.0, 32.0
# Pocket centres sit PITCH apart; END is the bar between outer pockets and
# board ends. Bar root stress scales with 1/width^2: the end bars carry the
# outermost edges, and at 11 mm (the middle bars are 16) FEA put them at twice
# the middle bars' stress, so they are 15 mm.
PITCH, END = 48.0, 15.0
# Rope diameter the channels are sized for. The straight bore leaves BORE_GAP
# all round the cord, for threading; the trough at the exits leaves TROUGH_GAP.
CORD = 8.0
BORE_GAP, TROUGH_GAP = 0.4, 0.2
# Hanging tilts the board until the fingers sit below where the strands leave
# its top end, so the further the rope runs behind the fingers, the more each
# edge tips towards the climber, into a sloper. The rope axis therefore sits as
# far forward as the end lips' cover over it allows (see build), but no
# further than the middle of the shallowest edge's grip face, so with evenly
# spread finger pressure no edge tips into an incut. It never sits lower than
# ROPE_Z_MIN, 2 mm above the floor plane, which sets the minimum edge depth.
ROPE_Z_MIN = BACK + 2
# Side rail between the pockets and the bore. A thicker cord moves the channels
# outwards instead of thinning the rail, so everything inboard of the bore,
# the exit rounds included, stays put and the board widens.
RAIL = 8.6
# Minimum material between the rope channel and the outside: the front over
# the exits, the side wall beside the bore. The board ends at the side wall's
# outside: nothing outboard of it carries load.
COVER = 2.0
# Each channel exit is rounded towards the board centre with EXIT_R, where the
# rope turns: 90 degrees under the board, the strand angle towards the anchor.
# Bearing stress and layer tension there scale with 1/EXIT_R. The turn runs in
# a trough closer to the cord than the bore, to widen the contact. Other bore
# mouth edges round with EXIT_RIM.
EXIT_R, EXIT_RIM = 15.0, 0.8
# The trough carries on across the end face as a TRACK-deep groove to the other
# exit, so the loop completes its 90 degree turn on EXIT_R and runs on under
# the board without crossing an edge. One sweep per end makes the round, the
# track and their junction, avoiding an EXIT_R round exactly tangent to the
# end face, which OCCT booleans mis-handle.
TRACK = 1.0
# For the same reason the trough's bearing side starts 0.1 mm outside the bore
# wall, and the EXIT_RIM round crosses the end face 0.05 mm short of tangency.
SWEEP_OVERSIZE, RIM_DIP = 0.1, 0.05
# Corners outside the rope's turn carry no load, and covering the exits there
# needs bridging. A cut at 45 degrees opens the exits, leaving the end face flat
# to END_FACE from the centre: past where the track meets the exit, 4.5 mm
# clear of the EXIT_R round, with a closed tunnel behind it. The cut's edges
# round with CORNER_R.
END_FACE, CORNER_R = 55.0, 2.5
# The rope is enclosed only in COLLAR-long tunnels at each end, around the
# exits, which are also full width. Between them it runs straight and presses
# on nothing, so above the rope axis the side is cut back to a shelf wall,
# leaving an open half-pipe seat: nothing to bridge when printing, and a short
# tunnel to thread. COLLAR leaves 3 mm beyond the EXIT_R trough. The shelf wall
# sits SHELF_IN outboard of the bore's inner side, so its root and fillet fall
# inside the bore.
COLLAR, SHELF_IN = 19.0, 0.8
# In the collars, above the rope axis, a tube wraps the channel. It stands
# TUBE_PROUD proud of the side, so the side plane cuts it rather than touching
# it tangentially, which OCCT booleans mis-handle.
TUBE_PROUD = 0.4
# Concave root fillet where the pocket walls meet the floor. Hanging loads the
# edge as a cantilever from Z=BACK, with peak tension across print layers at
# this root. R2 is far below fingertip radius, so usable edge depth is kept.
ROOT_R = 2.0
# Grip edges, where the fingers wrap over a lip into its pocket, round with
# GRIP_R, which comes off the nominal edge depth; every other edge rounds with
# EDGE_R. Each lip stays level for GRIP_FLAT beyond its grip round.
GRIP_R, EDGE_R, GRIP_FLAT = 3.0, 0.8, 1.0
POCKET_CORNER_R = 5.0
# The front clears the collar tubes by TUBE_STEP, room for EDGE_R at the top
# and root of the step between them; OCCT fails the fillet under 2 mm.
TUBE_STEP = 2.0
# Depth labels centre LABEL_U from the pocket edge, just beyond the grip
# round, recessed 0.6 mm below the front wherever it slopes.
LABEL_U = GRIP_R + 2.1


def front_profile(H, pockets):
    """[y0,y1,z0,z1] spans of the front: level where z0==z1, else an S of two
    equal arcs, level at both ends (variants.front_height), so the front changes
    height without a step. Each lip is level from its grip edge to GRIP_FLAT
    past its grip round. Beside a pocket the front changes height between the
    pocket's corners, so its rim is smooth all round; across a bar, between
    the lips' level parts."""
    g, c = GRIP_R + GRIP_FLAT, POCKET_CORNER_R
    level = []
    for y, lo, hi in pockets:
        level += [
            [y - PH / 2 - g, y - PH / 2 + c, BACK + lo],
            [y + PH / 2 - c, y + PH / 2 + g, BACK + hi],
        ]
    level[0][0], level[-1][1] = -H / 2, H / 2
    spans = []
    for a, b in itertools.pairwise(level):
        spans += [[a[0], a[1], a[2], a[2]], [a[1], b[0], a[2], b[2]]]
    spans.append([level[-1][0], level[-1][1], level[-1][2], level[-1][2]])
    merged = []
    for s in spans:
        if merged and merged[-1][2] == merged[-1][3] == s[2] == s[3]:
            merged[-1][1] = s[1]
        else:
            merged.append(s)
    return merged


def front_blank(W, H, spans):
    """Side profile under the front, extruded across the board's width."""
    wp = (
        cq.Workplane("YZ", origin=(-W / 2, 0, 0))
        .moveTo(-H / 2, 0)
        .lineTo(-H / 2, spans[0][2])
    )
    for y0, y1, z0, z1 in spans:
        if z0 == z1:
            wp = wp.lineTo(y1, z1)
            continue
        L, h = y1 - y0, z1 - z0
        r = math.copysign((L * L + h * h) / (4 * abs(h)), h)
        m = ((y0 + y1) / 2, (z0 + z1) / 2)
        for p, q, c in [((y0, z0), m, (y0, z0 + r)), (m, (y1, z1), (y1, z1 - r))]:
            # Arc midpoint, on the bisector of the radii to its ends.
            vy, vz = p[0] + q[0] - 2 * c[0], p[1] + q[1] - 2 * c[1]
            k = abs(r) / math.hypot(vy, vz)
            wp = wp.threePointArc((c[0] + vy * k, c[1] + vz * k), q)
    return wp.lineTo(H / 2, 0).close().extrude(W)


def round_edges(body, pockets):
    """Fillets every edge: the pocket rims with GRIP_R, everything else with
    EDGE_R."""
    solid = body.val()
    grips = [
        e
        for e in solid.Edges()
        if e.geomType() == "LINE"
        and abs(e.Length() - (PW - 2 * POCKET_CORNER_R)) < 1e-6
        and abs(e.Center().x) < 1e-6
        and any(
            abs(e.Center().y - (y + side * PH / 2)) < 1e-6
            and abs(e.Center().z - (BACK + d)) < 1e-6
            for y, lo, hi in pockets
            for side, d in [(-1, lo), (1, hi)]
        )
    ]
    assert len(grips) == 2 * len(pockets), len(grips)
    fillet = BRepFilletAPI_MakeFillet(solid.wrapped)
    for grip in grips:
        # Both grip edges of a pocket lie on its one smooth rim.
        if fillet.Contour(grip.wrapped):
            continue
        fillet.Add(GRIP_R, grip.wrapped)
        assert fillet.Closed(fillet.NbContours())
    for e in solid.Edges():
        if not fillet.Contour(e.wrapped):
            fillet.Add(EDGE_R, e.wrapped)
    fillet.Build()
    assert fillet.IsDone()
    return cq.Workplane(obj=cq.Shape.cast(fillet.Shape()))


def build(depths, cord=CORD):
    # Sizes that follow the cord.
    ROPE_R, TROUGH_R = cord / 2 + BORE_GAP, cord / 2 + TROUGH_GAP
    ROPE_X = PW / 2 + RAIL + ROPE_R
    W = 2 * (ROPE_X + ROPE_R + COVER)
    CHAMFER = W / 2 - END_FACE
    SHELF_X = ROPE_X - ROPE_R + SHELF_IN
    TUBE_R = ROPE_R + COVER + TUBE_PROUD
    # At the ends the front must cover the exits by COVER, and clear the collar
    # tubes by a rounded step: CLEAR above the rope axis.
    CLEAR = max(ROPE_R + EXIT_RIM + COVER, TUBE_R + TUBE_STEP)
    MIN_DEPTH = ROPE_Z_MIN + CLEAR - BACK
    assert len(depths) % 2 == 0, (
        f"{depths}: give depths in pairs, lower,upper per pocket"
    )
    assert min(depths) >= MIN_DEPTH - 1e-9, (
        f"{depths}: depths under {MIN_DEPTH:g} mm leave too little material over the rope channels"
    )
    ROPE_Z = min(
        BACK + min(depths[0], depths[-1]) - CLEAR,
        BACK + (ROOT_R + min(depths) - GRIP_R) / 2,
    )
    n = len(depths) // 2
    H = n * PH + (n - 1) * (PITCH - PH) + 2 * END
    # Bottom to top: center Y, lower lip depth, upper lip depth.
    pockets = [
        ((i - (n - 1) / 2) * PITCH, depths[2 * i], depths[2 * i + 1]) for i in range(n)
    ]
    ZMAX = BACK + max(depths)
    name = "hangboard_" + dirname(depths)
    out = here / dirname(depths)
    out.mkdir(exist_ok=True)
    print(
        "Building",
        name,
        f"for a Ø{cord:g} mm cord, rope axis at Z={ROPE_Z:g} mm",
        flush=True,
    )
    spans = front_profile(H, pockets)
    # An S rising more than it runs would overhang.
    for y0, y1, z0, z1 in spans:
        assert abs(z1 - z0) <= y1 - y0, (
            f"{depths}: lips {z0 - BACK:g} and {z1 - BACK:g} differ by more than the {y1 - y0:g} mm between them"
        )
    envelope = (
        cq.Workplane("XY")
        .box(W, H, ZMAX, centered=(True, True, False))
        .edges("|Z")
        .chamfer(CHAMFER)
        .edges("|Z")
        .fillet(CORNER_R)
    )
    blank = front_blank(W, H, spans)
    body = envelope.intersect(blank)
    COLLAR_Y = H / 2 - COLLAR
    shelf = (
        cq.Workplane("XY")
        .box(W / 2 + 10 - SHELF_X, 2 * COLLAR_Y, ZMAX + 2 - ROPE_Z, centered=False)
        .translate((SHELF_X, -COLLAR_Y, ROPE_Z))
    )
    body = body.cut(shelf).cut(shelf.mirror("YZ"))
    print("Open rope seats valid", body.val().isValid(), flush=True)
    # In the collars, above and outboard of the rope axis, only a tube wall
    # encloses the rope; the block around it carried no load.
    tube = cq.Solid.makeCylinder(
        TUBE_R, H + 2, cq.Vector(ROPE_X, -H / 2 - 1, ROPE_Z), cq.Vector(0, 1, 0)
    )
    quarter = (
        cq.Workplane("XY")
        .box(W / 2 + 10 - ROPE_X, COLLAR + 1, ZMAX + 2 - ROPE_Z, centered=False)
        .translate((ROPE_X, COLLAR_Y, ROPE_Z))
        .cut(tube)
    )
    for q in [
        quarter,
        quarter.mirror("YZ"),
        quarter.mirror("XZ"),
        quarter.mirror("YZ").mirror("XZ"),
    ]:
        body = body.cut(q)
    print("Collar tubes valid", body.val().isValid(), flush=True)
    for y, _, _ in pockets:
        cutter = (
            cq.Workplane("XY")
            .box(PW, PH, ZMAX - BACK + 6, centered=(True, True, False))
            .translate((0, y, BACK))
            .edges("|Z")
            .fillet(POCKET_CORNER_R)
        )
        cutter = cutter.faces("<Z").edges().fillet(ROOT_R)
        body = body.cut(cutter)
    print("Raw body valid", body.val().isValid(), flush=True)
    body = round_edges(body, pockets)
    print("Rounded body valid", body.val().isValid(), flush=True)
    # Straight see-through channels, so the rope can leave either end straight.
    # Half-section (radius, axial Y) revolved about the channel axis; both
    # ends round out with EXIT_RIM into the end faces.
    a, b, s = (
        ROPE_R + EXIT_RIM,
        ROPE_R + EXIT_RIM + 1,
        EXIT_RIM * (1 - 1 / math.sqrt(2)),
    )
    section = (
        cq.Workplane("XY")
        .moveTo(0, -H / 2 - 2)
        .lineTo(b, -H / 2 - 2)
        .lineTo(b, -H / 2 - RIM_DIP)
        .lineTo(a, -H / 2 - RIM_DIP)
        .threePointArc(
            (ROPE_R + s, -H / 2 + s - RIM_DIP), (ROPE_R, -H / 2 + EXIT_RIM - RIM_DIP)
        )
        .lineTo(ROPE_R, H / 2 - EXIT_RIM + RIM_DIP)
        .threePointArc((ROPE_R + s, H / 2 - s + RIM_DIP), (a, H / 2 + RIM_DIP))
        .lineTo(b, H / 2 + RIM_DIP)
        .lineTo(b, H / 2 + 2)
        .lineTo(0, H / 2 + 2)
        .close()
    )
    channel = section.revolve(360, (0, 0, 0), (0, 1, 0)).val()
    for sx in [-1, 1]:
        body = body.cut(channel.translate(cq.Vector(sx * ROPE_X, 0, ROPE_Z)))
    # At each end, one TROUGH_R sweep leaves one channel, turns towards the
    # centre around a round of EXIT_R, crosses the end face as the TRACK and
    # turns back into the other channel. A rope turning inwards bears on that
    # round, not on a 90 degree edge.
    Rb = EXIT_R + TROUGH_R
    cx = ROPE_X - ROPE_R - SWEEP_OVERSIZE - EXIT_R
    for sy in [-1, 1]:
        cy = sy * (H / 2 - TRACK - EXIT_R)
        V = lambda sx, t: cq.Vector(
            sx * (cx + Rb * math.cos(t)),
            cy + sy * Rb * math.sin(t),  # noqa: B023
            ROPE_Z,
        )
        path = cq.Wire.assembleEdges(
            [
                cq.Edge.makeThreePointArc(
                    V(1, 0), V(1, math.pi / 4), V(1, math.pi / 2)
                ),
                cq.Edge.makeLine(V(1, math.pi / 2), V(-1, math.pi / 2)),
                cq.Edge.makeThreePointArc(
                    V(-1, math.pi / 2), V(-1, math.pi / 4), V(-1, 0)
                ),
            ]
        )
        loop = (
            cq.Workplane("XZ", origin=V(1, 0).toTuple())
            .circle(TROUGH_R)
            .sweep(path, transition="right")
        )
        assert loop.val().isValid()
        body = body.cut(loop)
    print("Rope channels valid", body.val().isValid(), flush=True)
    # Nominal lip depth labels, upper set rotated for use after a half turn.
    # Each is a tall glyph prism, cut back to the front lowered by 0.6 mm.
    sunk = blank.translate((0, 0, -0.6))
    for y, dlo, dhi in pockets:
        for yy, depth, angle in [
            (y - PH / 2 - LABEL_U, dlo, 0),
            (y + PH / 2 + LABEL_U, dhi, 180),
        ]:
            label = cq.Workplane("XY").text(
                f"{depth:g}",
                5,
                ZMAX + 2,
                font="DejaVu Sans",
                kind="bold",
                combine=False,
            )
            label = label.rotate((0, 0, 0), (0, 0, 1), angle)
            # Centre the glyphs themselves, not the font's line box.
            label = label.translate(
                (0, yy - label.val().BoundingBox().center.y, 0)
            ).cut(sunk)
            body = body.cut(label)
    shape = body.val()
    assert shape.isValid() and len(shape.Solids()) == 1
    cq.exporters.export(
        body, str(out / f"{name}.stl"), tolerance=0.04, angularTolerance=0.08
    )
    cq.exporters.export(body, str(out / f"{name}.step"))
    clean(out / f"{name}.stl")
    # Illustrative cord, straight through both channels and 20 mm beyond.
    rope = cq.Compound.makeCompound(
        [
            cq.Solid.makeCylinder(
                cord / 2,
                H + 40,
                cq.Vector(sx * ROPE_X, -H / 2 - 20, ROPE_Z),
                cq.Vector(0, 1, 0),
            )
            for sx in [-1, 1]
        ]
    )
    cq.exporters.export(
        rope, str(out / "rope-preview.stl"), tolerance=0.1, angularTolerance=0.12
    )
    config = {
        "name": name,
        "depths_mm": depths,
        "dimensions_mm": [W, H, ZMAX],
        "pockets": pockets,
        "pocket_size_mm": [PW, PH],
        "floor_z_mm": BACK,
        "pocket_root_radius_mm": ROOT_R,
        "edge_radius_mm": EDGE_R,
        "grip_edge_radius_mm": GRIP_R,
        "grip_flat_mm": GRIP_FLAT,
        "label_offset_mm": LABEL_U,
        "front_spans_mm": spans,
        "corner_radius_mm": CORNER_R,
        "cord_diameter_mm": cord,
        "channel_radius_mm": ROPE_R,
        "rope_x_mm": ROPE_X,
        "rope_z_mm": ROPE_Z,
        "exit_radius_mm": EXIT_R,
        "exit_trough_radius_mm": TROUGH_R,
        "exit_rim_radius_mm": EXIT_RIM,
        "track_depth_mm": TRACK,
        "exit_sweep_oversize_mm": SWEEP_OVERSIZE,
        "corner_chamfer_mm": CHAMFER,
        "tube_outer_radius_mm": TUBE_R,
        "exit_front_cover_min_mm": COVER,
        "collar_length_mm": COLLAR,
        "shelf_x_mm": SHELF_X,
        "print_orientation": "flat rear Z=0 on bed; finger pockets face +Z",
    }
    (out / "parameters.json").write_text(json.dumps(config, indent=2))
    print("Export complete; volume cm3", shape.Volume() / 1000, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build hangboard variants.")
    parser.add_argument(
        "depths", nargs="*", default=[DEFAULT], help="edge depths, e.g. 20,15"
    )
    parser.add_argument(
        "--cord",
        type=float,
        default=CORD,
        help=f"rope diameter in mm (default {CORD:g})",
    )
    args = parser.parse_args()
    for spec in args.depths:
        build(parse(spec), args.cord)
