# Reciprocating Drill Attachment

3D-printable reciprocating attachment for a hand drill using a self-reversing screw mechanism. Converts continuous drill rotation into linear back-and-forth motion. A 50mm diameter flat platform on top accepts interchangeable attachments (sanding pads, scrapers, etc.).

## Mechanism

A self-reversing screw has a sinusoidal groove on a cylinder. A follower pin rides in the groove and is constrained to move only linearly along Z. As the drill spins the screw, the pin (and attached slider) reciprocates up and down.

The slider rides in a vertical pocket cut into the housing wall. A pin passes through a slit in the inner wall to engage the groove. A stem passes through the outer wall, connecting to an arm that carries the platform above the housing.

## Parts

| Part | File | Description |
|------|------|-------------|
| Screw | `screw.stl` | Cylinder with sinusoidal helical groove and 6mm drill chuck shank |
| Housing | `housing.stl` | Cylindrical body with bore, vertical pocket, pin slit, and stem slot |
| Slider | `slider.stl` | Body in pocket, follower pin, stem, arm, and 50mm platform (4x M4 holes) |
| Cap | `cap.stl` | Bottom cap with press-fit lip; retains the screw axially |

## Parameters

### Screw
- Outer diameter: 20mm
- Length: 60mm
- Shank: 6mm x 20mm (fits drill chuck)
- Groove: 4mm wide, 3mm deep, semicircular cross-section
- Stroke: 25mm total reciprocating travel
- Reversals: 2 full back-and-forth cycles per revolution

### Housing
- Outer diameter: 50mm, bore: 20.4mm (0.4mm clearance)
- Length: 65mm
- Inner wall: 2mm (bore side of pocket)
- Outer wall: 3mm (OD side of pocket)
- Pocket: 9.8mm radial x 12mm tangential, Z 5-55mm
- Pin slit: 4mm wide through inner wall
- Stem slot: 8.4mm wide through outer wall, open at top

### Slider
- Body: 9.4mm radial x 11.6mm tangential x 25mm tall (rides in pocket)
- Follower pin: 3.0mm diameter, 5mm long
- Stem: 2.7mm radial x 8mm tangential (bridges to outer wall)
- Arm: 5mm radial x 8mm tangential x 38mm tall (outside housing)
- Platform: 50mm diameter, 4mm thick
- 4x M4 clearance holes on 35mm bolt circle

### Cap
- Diameter: 50mm, thickness: 5mm
- Shank bore: 6.4mm (0.4mm clearance)
- Press-fit lip: 3mm tall, 0.3mm interference (20.7mm in 20.4mm bore)

## Building

```bash
uv venv
source .venv/bin/activate
uv pip install cadquery
python recipro_driller.py
```

Produces 4 STL files in the project directory.
