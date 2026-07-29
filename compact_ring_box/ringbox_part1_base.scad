// =====================================================================
//  FLAT RING BOX - PART 1: base
//  Ring nest, halo pocket (lower half), pedestal + locating post,
//  register lip and the two lower magnet pockets.
//  Rendered in print orientation: floor down, lip up.
// =====================================================================
include <ringbox_common.scad>

module base() {
    union() {
        difference() {
            union() {
                linear_extrude(base_h) profile2d();
                translate([0, 0, base_h]) linear_extrude(lip_h)
                    difference() {
                        offset(r = -lip_inset) profile2d();
                        corners2d(corner_r);          // open corners for the magnets
                    }
            }
            cavity();                         // ring nest + head slot, through the lip
            magnet_holes(base_h - magnet_t - magnet_gap);
            thumb_notch();
        }
        // pedestal + locating post (added after the nest was cut)
        difference() {
            union() {
                translate([x0, 0, floor_t - 0.01]) cylinder(d = ped_d, h = band_bot - floor_t + 0.01);
                translate([x0, 0, band_bot])       cylinder(d = post_d, h = post_top - band_bot - 0.8);
                translate([x0, 0, post_top - 0.8]) cylinder(d1 = post_d, d2 = post_d - 1.6, h = 0.8);
            }
            head_slot(0.2);                   // relief only where the halo passes
        }
    }
}

base();
