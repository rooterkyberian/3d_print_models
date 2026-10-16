# Hangboard

Portable stepped-lip hangboard, generated for any set of edge depths.
Custom CAD geometry; a prototype with no verified load capacity.
Units: mm. Z axis: thickness; grip side: +Z; back: Z=0.

![preview](24-22-20-18-16-14/preview.png)

## Choosing edge depths

```bash
python build.py 24,22,20,18,16,14 20,15 25,20,17,14
python build.py --cord 6 20,15
```

- Depths are read bottom to top, in pairs, one pair per pocket: first the lower edge (used with the board upright), then the upper edge (used after turning the board upside down).
- Give an even number of depths. Each must be at least 6.8 mm plus half the cord diameter (10.8 mm for the default 8 mm cord), so the front keeps 2 mm of material over the rope channels and room for a rounded step above the tubes at the ends. That is with the rope at its lowest; deeper end lips let it sit further forward (see Rope).
- The two depths of a pocket may differ by up to 22 mm, and the depths either side of a bar between pockets by up to 8 mm: the front changes height over those lengths (see Grip layout), and a larger difference would overhang.
- The board height follows the pocket count: 32 mm pockets on a 48 mm pitch, plus a 15 mm bar at each end. The end bars carry the outermost edges; at 11 mm, FEA of an earlier version put them at twice the stress of the 16 mm middle bars.
- Each build goes to a directory named after its depths, e.g. `20-15/`. Without arguments, `build.py` builds `24,22,20,18,16,14`.
- `--cord` sets the rope diameter the channels are sized for; the default is 8 mm (see Rope). It is recorded in `parameters.json`, not in the directory name, so rebuilding a variant with another cord replaces it.

| Depths | Pockets | Outline W x H x max. thickness (8 mm cord) | Rope axis |
|--------|---------|--------------------------------|-----------|
| `24,22,20,18,16,14` | 24/22, 20/18, 16/14 | 138.8 x 158 x 31 mm | Z=12.2 mm |
| `25,20,17,14` | 25/20, 17/14 | 138.8 x 110 x 32 mm | Z=12.2 mm |
| `20,15` | 20/15 | 138.8 x 62 x 27 mm | Z=13.2 mm |

## Grip layout

- Each pocket is a nominal 100 x 32 mm slot, and each lip sits at its own height.
- Between lips the front changes height in smooth S-curves of two equal arcs, not steps. Beside each pocket, on the side rails, the change runs between the pocket's rounded corners, so the rim stays level around them. Across each bar between pockets, it runs from 1 mm past one grip round to 1 mm before the next. Every grip edge keeps its nominal height.
- The upper labels are rotated 180° so they read correctly when the board is turned upside down.
- Pocket floors are flat at Z=7 mm; the depth differences come from extending the entry lips. The height changes do not split the pocket interior into two levels.
- Grip edges, where the fingers wrap over a lip: R3 mm, all round each pocket's rim. The round comes off the nominal depth, so the flat part of each edge is 3 mm shallower than its label.
- Other edges: R0.8 mm; pocket corners: R5 mm.
- Where the pocket walls meet the floor: R2 mm root fillet. Hanging loads each edge as a cantilever from the floor, with peak tension across the print layers at this root; the larger radius lowers that stress concentration. It is much smaller than a fingertip, so the usable edge depth is unchanged.
- Depths are nominal, before edge rounding.
- Labels: 5 mm text, centred 5.1 mm from the pocket edge just past the grip round, recessed 0.6 mm and following the front where it slopes.

## Sides

- The board ends at the outside of the rope channel's 2 mm wall: material outboard of it carried no load. The sides are flat and vertical relative to the print bed; there are no overhangs.
- The outer front and back edges are rounded R0.8 mm.
- The corners are cut off at 45°, 14.4 mm along each side with the 8 mm cord, so the end faces reach 55 mm from the centre, with the cut's edges rounded R2.5 mm. Outside the rope's turn they carried no load, and covering the rope exits there needed bridging. The cut opens the exits. It stays clear of the rope's bearing round and leaves a closed tunnel behind it.
- Within 19 mm of each end, a collar encloses the rope. Below the rope axis it has the 2 mm side wall; above the axis, only a tube wall wraps the channel. The tube's outer radius is 6.8 mm with the 8 mm cord, 0.4 mm proud of the side, so the side plane slices it at a shallow angle instead of touching it tangentially.
- Between the collars, the side above the rope axis is cut back to 0.8 mm outside the channel's inner edge. That leaves the rope an open half-pipe seat with a 2 mm outer wall (see Rope).

## Dimensions

- Width 122.8 mm plus twice the cord diameter: 138.8 mm with the 8 mm cord. Height from the pocket count (see above).
- Thickness: 7 mm plus the lip depth, so it changes along the board; the maximum is 7 mm plus the deepest edge.
- The back stays flat to sit on the print bed. The grip side changes height between the lips.
- Thickness under the pocket floors: 7 mm. FEA of an earlier 10 mm floor found it lightly loaded, at about a tenth of PLA's in-layer strength at 100 kg. Its bending stress scales with 1/thickness², so 7 mm roughly doubles that.

## Print orientation

- Place the flat back (Z=0) on the bed, with the finger pockets facing up (+Z).
- The rope runs horizontally in this orientation. Only the collars are closed: a tube from the collar's inner end to the corner cut, with a short bridged roof. With the 8 mm cord it is 6.6 mm long on its outer side and 15.4 mm on its inner side, as the cut is at 45°. Check it in the slicer. The open seats between them print without overhangs.
- No layer simulation or test print has been done; the model as a whole is not claimed to be support-free.

## Rope

- Intended rigging: one rope loop with a single knot at the anchor. The rope runs from the anchor down one side of the board, under the bottom, up the other side and back to the anchor. No knot rests on the board, and the anchor is always narrower than the board, so the strands angle inwards.
- Each side has a straight channel 0.8 mm wider than the cord, so Ø8.8 mm for the default 8 mm cord, running the full height parallel to the back and see-through end to end (`bottom.png`). The rope leaves straight whichever way up the board hangs.
- Rope height: hanging tilts the board until the fingers sit directly below where the strands leave its top end. The further the rope runs behind the fingers, the more each edge tips towards the climber, into a sloper. An FEA-based estimate for 20-15 with the rope at Z=9 mm put that at about 10° for the 20 mm edge and 7° for the 15 mm edge, assuming evenly spread finger pressure.
- So the rope axis sits as far forward as the shallower end lip allows, keeping 2 mm of front over the exits and a rounded step above the collar tubes: 8.8 mm under that lip's front with the 8 mm cord. Only the end lips limit it; the middle lips stay well clear of the channel. It goes no further forward than the middle of the shallowest edge's grip face, so with evenly spread pressure no edge tips into an incut, and never lower than 2 mm above the floor plane (Z=9 mm). The table above lists it per variant.
- The rope is enclosed only in 19 mm collars at each end, which keep it captive and are short to thread. Between them it runs straight and presses on nothing, so it lies in an open half-pipe seat with no outer wall.
- Each exit opens towards the board centre with an R15 mm round. The rope bears on it where it turns: 90° under the board at the lower exits, and the strand angle towards the anchor at the upper ones. The rounds are the same at both ends, so the board can be flipped.
- Bearing stress and layer tension at the turn scale with 1/radius. FEA of the earlier R9.6 rounds suggested R15 cuts both by about 35%, and it is kinder to the rope.
- Along the turn the rope runs in a trough 0.4 mm wider than the cord (Ø8.4 mm), closer to it than the bore, which widens the contact. The straight bore keeps 0.4 mm all round for threading.
- A thicker cord moves the channels outwards rather than thinning the 8.6 mm rail between the pockets and the bore, so the pockets and the R15 rounds stay put and the board widens. The corner cut, the side wall and the collar tubes follow the channel.
- The bore leaves through the corner cut. Its edge there is not rounded, but the rope does not bear on it: the rope bears on the inner round.
- Past the round, the turn continues across each end face as a 1 mm deep track to the other exit. Under the board, the loop completes its whole 90° turn on R15 and then lies in the track: it never turns over an edge, and it stays centred on the end face.
- One sweep per end makes the round and the track, so nothing in the build relies on a surface exactly tangent to the end face. OpenCASCADE booleans mis-handle those. For the same reason, the trough's bearing side starts 0.1 mm outside the bore wall, a step below print resolution.

## Files

| File | Description |
|------|-------------|
| `build.py` | CadQuery source: `python build.py [DEPTHS ...]`. |
| `variants.py` | Depth lists, their output directories and the front profile, shared by the scripts. |
| `clean_stl.py` | Cleans up numerically collapsed export triangles at a 0.00001 mm tolerance. |
| `verify.py` | Geometry checks; writes `verification.json`. |
| `render.py` | STL renderer; label recesses are darkened for legibility only. |
| `section.py` | Section extracted from the STL and rope channel diagram. |

`verify.py`, `render.py` and `section.py` take the same depth lists as `build.py`, and process every built variant when given none. Each variant directory holds:

| File | Description |
|------|-------------|
| `hangboard_<depths>.stl` | Model for the slicer, without the rope model. Generated, not committed. |
| `hangboard_<depths>.step` | CAD solid for editing. Generated, not committed. |
| `rope-preview.stl` | ONLY an illustrative model of the cord; do not print it as part of the hangboard. Generated, not committed. |
| `parameters.json` | Model parameters. |
| `verification.json` | Result of `verify.py`. |
| `preview.png` / `front.png` / `rope-exits.png` / `side.png` / `bottom.png` / `section-and-rope.png` | Previews. `bottom.png` looks along the rope channels; `side.png` shows the collar tubes and open seats. |

Dependencies: CadQuery (tested with 2.8), NumPy, Pillow; additionally SciPy for `verify.py` and Matplotlib for `section.py`.

## Verification scope

- Checked for each variant: STEP solid validity and dimensions, every edge depth, flat floors, the R2 root fillets, the R3 grip rounds and pocket clearance.
- The front follows its profile, level or in S-curves, across the bars and along both side rails. Each label is recessed 0.6 mm below the front, with no recess on the grip round.
- Rope: rays within 0.2 mm of each nominal bore cross the whole board unobstructed. The R15 exit rounds have material just inside and air just outside through the whole 90° turn. A clear path of the cord's diameter follows each exit's turn until it leaves the board. The track is 1 mm deep across each end face, which is flat beside it. The corner cuts sit at their nominal position.
- Collars: closed for 19 mm at each end, reaching the side below the rope axis, a tube of the nominal wall above it, and open just beyond. Between them: reaching the side below the rope axis, the side cut back above it, and a half-pipe seat of the nominal radius.
- STL topology.
- The result is saved in each variant's `verification.json`.

## Limitations

- No test print, mechanical tests or rope wear testing have been done. Load capacity is not verified.
- The channels and fillets are geometrically correct; once printed, their surface and whether they stay clear depend on the printer and its settings. Inspect the channels in the slicer's layer preview and clean up the surfaces the rope touches.
- Scaling the model changes the grip depths, channels and wall thicknesses at the same time.
