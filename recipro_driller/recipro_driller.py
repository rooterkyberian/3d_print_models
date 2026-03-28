"""
Recipro Driller - Redesigned 50mm Travel Attachment
Architecture:
1. Screw (Internal): Sinusoidal reversing groove + Hex Shank.
2. Slider (Middle): Tube with follower pin + anti-rotation keys.
3. Housing (Outer): Guide slots + Drill neck clamp (43mm).
"""

import math
import cadquery as cq

# ── Parameters ───────────────────────────────────────────────────────

# Global
stroke = 50.0
clearance = 0.4

# Screw
screw_d = 24.0          
screw_length = 110.0
shank_d = 6.35          
shank_length = 30.0
groove_w = 6.5          
groove_depth = 4.5

# Slider
slider_wall = 5.0       
slider_length = 50.0
slider_id = screw_d + clearance
slider_od = slider_id + 2 * slider_wall
key_width = 12.0
key_height = 6.0        

# Housing
housing_id = slider_od + clearance
housing_wall = 3.0
housing_od = housing_id + 2 * housing_wall
housing_length = 130.0
neck_clamp_d = 43.0     # Standard drill neck diameter
neck_clamp_h = 25.0

# Derived
path_r = (screw_d / 2) - groove_depth + (groove_w / 2)

# ── 1. Screw ─────────────────────────────────────────────────────────

def make_screw():
    # Base Cylinder
    body = cq.Workplane("XY").circle(screw_d / 2).extrude(screw_length)
    
    # Hex Shank (extruded from Z=0 downwards)
    shank = cq.Workplane("XY").polygon(6, shank_d).extrude(-shank_length)
    
    # Transition
    transition = (
        cq.Workplane("XY")
        .workplane(offset=0.1).circle(screw_d/2)
        .workplane(offset=-5.1).polygon(6, shank_d)
        .loft()
    )
    
    screw_base = body.union(shank).union(transition)
    
    # --- Robust Groove Creation (Segmented Loft) ---
    n_points = 60
    path_pts = []
    for i in range(n_points + 1):
        theta = (i / n_points) * 2 * math.pi
        z_norm = 0.5 - 0.5 * math.cos(theta)
        z = z_norm * stroke + (screw_length - stroke) / 2
        path_pts.append((path_r * math.cos(theta), path_r * math.sin(theta), z))
    
    # Create profiles at each point
    profiles = []
    for i in range(n_points + 1):
        p = cq.Vector(path_pts[i])
        # Approximate tangent for orientation
        if i < n_points:
            p_next = cq.Vector(path_pts[i+1])
            tangent = (p_next - p).normalized()
        else:
            p_prev = cq.Vector(path_pts[i-1])
            tangent = (p - p_prev).normalized()
            
        plane = cq.Plane(origin=p, normal=tangent)
        # Create a circle wire
        wire = cq.Workplane(plane).circle(groove_w / 2).val()
        profiles.append(wire)
    
    # Loft segments and union them
    print("  Lofting groove segments...")
    groove_tool = None
    for i in range(n_points):
        # Create a solid by lofting between two wires
        segment = cq.Solid.makeLoft([profiles[i], profiles[i+1]], ruled=True)
        if groove_tool is None:
            groove_tool = segment
        else:
            groove_tool = groove_tool.fuse(segment)
    
    # groove_tool is now a Solid or Compound. 
    # To use .cut() on a Workplane, we wrap it.
    groove_tool_wp = cq.Workplane("XY").newObject([groove_tool])
    
    vol_before = screw_base.val().Volume()
    result = screw_base.cut(groove_tool_wp).clean()
    
    vol_after = result.val().Volume()
    print(f"Screw Volume: Before={vol_before:.2f}, After={vol_after:.2f}, Removed={vol_before - vol_after:.2f}")
    
    bb = result.val().BoundingBox()
    print(f"BB After: Z {bb.zmin:.2f} to {bb.zmax:.2f}")
    print(f"Screw Volume after cut:  {vol_after:.2f}")
    print(f"Volume removed:          {vol_before - vol_after:.2f}")
    
    if vol_after >= vol_before - 1.0: # Margin for floating point
        print("WARNING: Groove cut may have failed or removed negligible material.")
        # Fallback: Try a simpler boolean if needed, or check if tool is inverted

    return result

# ── 2. Slider ────────────────────────────────────────────────────────

def make_slider():
    # Tube
    slider = (
        cq.Workplane("XY")
        .circle(slider_od / 2)
        .circle(slider_id / 2)
        .extrude(slider_length)
    )
    
    # Anti-rotation keys (ears)
    keys = (
        cq.Workplane("XY")
        .rect(slider_od + 2 * key_height, key_width)
        .extrude(slider_length)
        .cut(cq.Workplane("XY").circle(slider_od / 2).extrude(slider_length))
    )
    
    slider = slider.union(keys)
    
    # Follower Pin Hole (threaded or press-fit)
    # Positioned at mid-length
    slider = slider.faces(">X").workplane().center(0, slider_length/2).circle(4.2/2).cutThruAll()
    
    # Top Platform for attachments
    platform = (
        cq.Workplane("XY")
        .workplane(offset=slider_length)
        .circle(50/2)
        .extrude(5)
    )
    # M4 Bolt pattern
    platform = platform.faces(">Z").workplane().rect(35, 35, forConstruction=True).vertices().circle(4.5/2).cutThruAll()
    
    return slider.union(platform)

# ── 3. Housing ───────────────────────────────────────────────────────

def make_housing():
    # Main Tube
    housing = (
        cq.Workplane("XY")
        .circle(housing_od / 2)
        .circle(housing_id / 2)
        .extrude(housing_length)
    )
    
    # Slots for Slider keys
    # Slots go from near bottom to top
    slot_start = 10
    slot_length = stroke + slider_length + 10
    
    slots = (
        cq.Workplane("XY")
        .workplane(offset=slot_start)
        .rect(housing_od + 10, key_width + clearance)
        .extrude(slot_length)
    )
    
    housing = housing.cut(slots)
    
    # Drill Neck Clamp
    # A larger diameter ring at the bottom with a slit for tightening
    clamp = (
        cq.Workplane("XY")
        .workplane(offset=-neck_clamp_h)
        .circle((neck_clamp_d + 15) / 2)
        .circle(neck_clamp_d / 2)
        .extrude(neck_clamp_h)
    )
    
    # Slit for clamping
    slit = (
        cq.Workplane("XY")
        .workplane(offset=-neck_clamp_h)
        .center(neck_clamp_d / 2 + 5, 0)
        .rect(20, 3)
        .extrude(neck_clamp_h)
    )
    
    # Bolt tabs for the clamp
    tabs = (
        cq.Workplane("XY")
        .workplane(offset=-neck_clamp_h)
        .center(neck_clamp_d / 2 + 5, 0)
        .rect(15, 20)
        .extrude(neck_clamp_h)
    )
    
    clamp = clamp.union(tabs).cut(slit)
    
    # Bolt hole for M5 clamping screw
    clamp = clamp.center(neck_clamp_d / 2 + 8, 0).workplane(offset=-neck_clamp_h/2).circle(5.5/2).cutThruAll()
    
    return housing.union(clamp)

# ── Export ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os
    out_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("Building redesigned recipro driller (Tube-over-Screw architecture)...")
    
    parts = {
        "screw": make_screw(),
        "slider": make_slider(),
        "housing": make_housing()
    }
    
    for name, shape in parts.items():
        path = os.path.join(out_dir, f"{name}.stl")
        cq.exporters.export(shape, path)
        print(f"  Saved {path}")

    print("Done.")
