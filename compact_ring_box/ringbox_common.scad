// =====================================================================
//  FLAT RING BOX - H-HV "Heaven" halo
//  Ring size 14 (ID 17.2 mm)  |  two-part magnetic clamshell
//  Units: mm
//
//  Idea: the ring lies FLAT (finger axis vertical) on a low pedestal,
//  a locating post goes through the bore, and the halo head parks in a
//  horizontal side pocket. Total height ~15 mm instead of the usual 45.
//  The only thing that sets the box height is the halo diameter.
//
//  Shared parameters + helper geometry for both halves. This file has
//  no top-level geometry of its own; render the part files instead:
//      ringbox_part1_base.scad  - base, pedestal and locating post
//      ringbox_part2_lid.scad   - lid
// =====================================================================

/* [Ring - VERIFY WITH CALIPERS, these are informed estimates] */
ring_id    = 17.2;  // finger hole diameter, size 14
band_th    = 1.8;   // band thickness (radial)
band_w     = 2.4;   // band width (along the finger)
head_d     = 9.0;   // widest diameter of the halo head (incl. prongs)
head_h     = 5.0;   // head height measured from the band OUTER surface
                    // (calipered at the thickest point, i.e. at the stone)

/* [Fit / clearances] */
clr        = 0.4;   // clearance around the head, vertical
side_clr   = 1.5;   // radial gap around the band (so you can pinch it out)
post_clr   = 0.6;   // gap between locating post and ring bore

/* [Shell] */
wall       = 2.0;
floor_t    = 1.4;   // floor of base = ceiling of lid
corner_r   = 4.0;   // outer corner radius (also the magnet pad radius)
lip_h      = 1.5;   // register lip height on the base
lip_inset  = 1.0;
lip_clr    = 0.15;  // fit clearance lip <-> lid recess

/* [Magnets - N42/N52 discs] */
magnet_d   = 5.0;
magnet_t   = 2.0;
magnet_fit = 0.15;  // added to diameter for a press fit
magnet_gap = 0.15;  // recess per side so magnets don't hold the seam open

/* [Lid decoration] */
heart_w    = 23.0;  // heart width across the lobes
heart_line = 1.2;   // width of the engraved contour
heart_cut  = 0.5;   // how deep it bites into the lid top
heart_a    = 270;    // 0 = tip down; 90 turns the tip to +X, the way the stone points,
                    // so the heart lies along the ring: lobes over the band, tip over
                    // the head - same taper as the cavity underneath

heart_text = "K&M";
text_font  = "Liberation Sans Narrow:style=Bold";
text_size  = 4.75;  // the band between the tip and the cleft caps this: at heart_w = 23
text_y     = 1.25;  // these clear the contour by 0.6 mm, which is the ridge that has to
                    // survive slicing.  Measured by boolean at $fn = 96 - nothing
                    // asserts it, so re-check after changing the string or either size

/* [Misc] */
notch_d    = 1.0;   // thumb scallop depth on the front face
post_up    = 2.0;   // how far the post sticks above the band centre plane
$fn        = 96;

// ---------------------------------------------------------------- derived
ring_od   = ring_id + 2*band_th;            // 20.8
reach     = ring_od/2 + head_h;             // axis -> stone table
nest_r    = ring_od/2 + side_clr;
head_r    = head_d/2 + clr;

ring_z    = floor_t + head_r;               // band centre plane = head axis height
base_h    = floor_t + magnet_t + magnet_gap;// seam: base is a tray, only deep enough
                                            // to bury the magnets - all the wall
                                            // height goes to the lid, so lifting it
                                            // leaves the ring standing in the open
lid_in    = ring_z + head_r - base_h;       // everything above the seam is lid
lid_h     = lid_in + floor_t;

end_slack = 1.2;   // spare material at the X ends
side_pad  = 1.2;   // spare material at the Y sides (wall around rear magnets)
                   // both sized so the corner magnets clear the ring nest -
                   // a bigger corner_r walks them inwards, see nest_wall below
box_x     = nest_r + reach + clr + 2*wall + 2*end_slack;
box_y     = 2*(nest_r + wall + side_pad);
x0        = -((reach + clr) - nest_r)/2;    // ring axis, X-centred cavity

ped_d     = ring_id + 1.4;                  // shoulder the band rests on
post_d    = ring_id - post_clr;
band_bot  = ring_z - band_w/2;
post_top  = ring_z + post_up;

cav_h     = ring_z + head_r - floor_t;      // interior height - note floor and ceiling
                                            // are both tangent to the head slot, which
                                            // is what lets the two fair into each other

mx        = box_x/2 - corner_r;
my        = box_y/2 - corner_r;

nest_wall = sqrt(pow(mx + x0, 2) + pow(my, 2)) - (magnet_d + magnet_fit)/2 - nest_r;
skin_wall = corner_r - (magnet_d + magnet_fit)/2;   // shell left over the magnet

// the cavity flares out to the slot along a line tangent to the chamber; that line is
// what the FRONT pair of magnets has to stay clear of (the rear pair sees nest_wall)
tip_v     = [reach + clr, head_r];                  // slot tip corner, from the ring axis
tan_n     = [cos(atan2(tip_v[1], tip_v[0]) + acos(nest_r/norm(tip_v))),
             sin(atan2(tip_v[1], tip_v[0]) + acos(nest_r/norm(tip_v)))];
flare_wall= tan_n * [mx - x0, my] - nest_r - (magnet_d + magnet_fit)/2;

assert(corner_r >= magnet_d/2 + 1.2, "corner_r too small for these magnets");
assert(nest_wall >= 1.0, "rear magnets break into the ring nest - raise end_slack/side_pad");
assert(flare_wall >= 1.0, "cavity flare runs into the front magnets");
assert(post_top + 1.0 < ring_z + head_r, "post reaches the lid ceiling");
assert(band_bot > base_h, "band sits below the tray rim - raise ring_z");
assert(floor_t - heart_cut >= 0.8, "heart engraving leaves too little lid ceiling");
echo(str("OUTER: ", box_x, " x ", box_y, " x ", base_h + lid_h, " mm"));
echo(str("split: ", base_h, " mm base tray + ", lid_h, " mm lid"));
echo(str("ring stands ", ring_z + head_r - base_h, " mm proud of the open base"));
echo(str("wall left to rear magnets: ", nest_wall, " mm, to front magnets: ", flare_wall, " mm"));
echo(str("shell over the magnet pockets: ", skin_wall, " mm"));
echo(str("lid ceiling under the heart: ", floor_t - heart_cut, " mm"));

// ---------------------------------------------------------------- 2D
module profile2d()      { offset(r = corner_r) square([box_x - 2*corner_r, box_y - 2*corner_r], center = true); }
module corners2d(r)     { for (sx = [-1,1], sy = [-1,1]) translate([sx*mx, sy*my]) circle(r = r); }

// ---------------------------------------------------------------- helpers
module head_slot(extra = 0) {                         // what the halo itself sweeps
    translate([x0 + ring_id/2, 0, ring_z])
        rotate([0, 90, 0])
            cylinder(r = head_r + extra, h = reach + clr - ring_id/2 + extra);
}

//  The whole interior as ONE convex volume: the ring chamber fairs straight out into
//  the head slot instead of the slot punching a hole through the chamber wall.  Both
//  bodies span floor_t..ring_z+head_r, so the hull keeps a flat roof and floor flush
//  with the lid ceiling and base floor, and its flanks come off the chamber on a
//  tangent - no step, no crease, just a teardrop in plan.
module cavity() {
    hull() {
        translate([x0, 0, floor_t]) cylinder(r = nest_r, h = cav_h);
        translate([x0 + reach + clr, 0, ring_z])
            rotate([0, 90, 0]) cylinder(r = head_r, h = 0.01);
    }
}

module magnet_holes(z0) {
    for (sx = [-1,1], sy = [-1,1])
        translate([sx*mx, sy*my, z0])
            cylinder(d = magnet_d + magnet_fit, h = magnet_t + magnet_gap + 0.02);
}

module thumb_notch() {                                // scallop across the front face
    translate([box_x/2 + 6 - notch_d, 0, base_h])
        rotate([90, 0, 0]) cylinder(r = 6, h = 16, center = true);
}
