// --- Dimensions ---
h = 9;      // Height of the pin (above the cap)
d = 6;        // Max diameter of the hooked pin
od = 26;      // Outer diameter of the base cap
ch = 1.5;     // Cap thickness / height

// --- Internal/Mechanism Parameters ---
shaft_d = 3.5;   // Diameter of the inner solid shaft
barb_count = 4;  // Number of hooks/barbs
slit_w = 1.2;    // Width of the slit creating the "U" shape

neck_h = 2;      // Height of the smooth neck below the barbs

$fn = 64; // Resolution for smooth circles
tip_h=0.5;

// 1. Define the original shape first
module pin_assembly() {
    union() {
        // Base Cap
        cylinder(h=ch, d=od);

        // Neck + Hooked Pin with slit through both
        barb_section_h = h - neck_h;
        translate([0, 0, ch]) {
            difference() {
                union() {
                    // Smooth neck
                    cylinder(h=neck_h, d=shaft_d);

                    // Barbed section
                    translate([0, 0, neck_h]) {
                        cylinder(h=barb_section_h, d=shaft_d);
                        barb_h = (barb_section_h - tip_h) / barb_count;
                        for(i = [0 : barb_count - 1]) {
                            translate([0, 0, i * barb_h])
                                cylinder(h=barb_h, d1=d, d2=shaft_d);
                        }
                        // Tapered Tip
                        translate([0, 0, barb_section_h - tip_h])
                            cylinder(h=tip_h, d1=shaft_d, d2=shaft_d - 1);
                    }
                }

                // Slit through neck and barbs
                translate([0, 0, h/2])
                    cube([d+2, slit_w, h+2], center=true);
            }
        }
    }
}

// 2. Orient for side-printing and cut the flat base
// Move the entire part up so the new flat cut rests exactly on the build plate (Z=0)
translate([0, 0, d/2])
difference() {
    // Lay the part on its side (Pin points along the X axis)
    rotate([0, 90, 0])
        pin_assembly();

    // Slice off everything that hangs below the pin's bottom edge
    // The pin's lowest point is at Z = -d/2. We cut away the cap below that point.
    translate([0, 0, -od/2 - d/2])
        cube([ (h+ch+neck_h)*3, od+5, od ], center=true);
}
