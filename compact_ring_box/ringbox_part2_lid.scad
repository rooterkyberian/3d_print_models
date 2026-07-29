// =====================================================================
//  FLAT RING BOX - PART 2: lid
//  Lip recess, band/post clearance, halo pocket (upper half) and the
//  two upper magnet pockets.
//
//  lid() is modelled mating-face-down at z = 0, opening upwards, so it
//  drops straight onto the base at z = base_h.  The top-level call
//  flips it for printing (flat outer top on the bed).
// =====================================================================
include <ringbox_common.scad>

//  classic parametric heart, x spans +/-16 and y -17..11.92, so scale by w/32 and
//  shift the midpoint of that y range back to zero to centre it on the lid
function heart_pt(t) = [16*pow(sin(t), 3),
                        13*cos(t) - 5*cos(2*t) - 2*cos(3*t) - cos(4*t)];

module heart2d(w) {
    scale(w/32) translate([0, -(11.92 - 17)/2])
        polygon([for (t = [0:2:358]) heart_pt(t)]);
}

module heart_outline(w, line) {                       // contour only, not a filled heart
    difference() {
        heart2d(w);
        offset(r = -line) heart2d(w);
    }
}

module lid() {
    difference() {
        linear_extrude(lid_h) profile2d();
        // recess that swallows the base lip
        linear_extrude(lip_h + 0.2)
            difference() {
                offset(r = -lip_inset + lip_clr) profile2d();
                corners2d(corner_r - lip_clr);        // solid magnet pads
            }
        // ring chamber + head slot, up to the ceiling
        translate([0, 0, -base_h]) cavity();
        magnet_holes(-0.01);
        translate([0, 0, -base_h]) thumb_notch();
        // engraved heart in the top face - that face lands on the bed when the lid is
        // printed flipped, so the contour comes out crisp with no bridging
        translate([0, 0, lid_h - heart_cut])
            linear_extrude(heart_cut + 0.1) rotate(heart_a) {
                heart_outline(heart_w, heart_line);
                translate([0, text_y]) text(heart_text, size = text_size,
                                            halign = "center", valign = "center",
                                            font = text_font);
            }
    }
}

translate([0, 0, lid_h]) rotate([180, 0, 0]) lid();
