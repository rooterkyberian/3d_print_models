import cadquery as cq
import recipro_driller as rd

# Re-create just the base body logic from recipro_driller.py for debugging
screw_r = rd.screw_r
screw_length = rd.screw_length
shank_d = rd.shank_d
shank_length = rd.shank_length

print(f"Building debug screw body...")
print(f"  Body: R={screw_r}, L={screw_length}")
print(f"  Shank: D={shank_d}, L={shank_length} (Hex)")

# 1. Main cylinder
screw_body = (
    cq.Workplane("XY")
    .circle(screw_r)
    .extrude(screw_length)
)

# 2. Hexagonal Shank
shank = (
    cq.Workplane("XY")
    .polygon(6, shank_d)
    .extrude(-shank_length)
)

# 3. Transition
transition = (
    cq.Workplane("XY")
    .workplane(offset=0.1)
    .circle(screw_r)
    .workplane(offset=-5.1)
    .polygon(6, shank_d)
    .loft()
)

# Union
body = screw_body.union(shank).union(transition)

# Check bounding box
bb = body.val().BoundingBox()
print(f"Bounding Box Z range: {bb.zmin} to {bb.zmax}")
print(f"Expected Z range: -{shank_length} to {screw_length}")

if abs(bb.zmin - (-shank_length)) < 0.1:
    print("SUCCESS: Shank is present in the geometry.")
else:
    print("FAILURE: Shank is missing from the geometry.")

# Export debug STL
cq.exporters.export(body, "debug_screw_base.stl")
print("Exported debug_screw_base.stl")
