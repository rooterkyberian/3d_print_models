// Front light holder cap
// compatible with Morezone Sports USB charging Bike Light

thickness = 1.5;
total_h = 3 * thickness;
id = 22.9;
space = 12;
screw_hole_center_distance = id / 2 - 5;
screw_hole_d = 2;
screw_hole_countersink_h = 0.1; // it was 1mm in orginal
screw_hole_countersink_d = 4;

friction_bump_r = 1;

inf = 30;
little_more = 0.1;

$fn = 64;

union() {
  difference() {
    cylinder(d = id + 2 * thickness, h = total_h);

    translate([ 0, 0, thickness ]) {
      difference() {
        cylinder(d = id, h = inf);
        translate([ -inf / 2, space / 2, thickness ]) cube([ inf, inf, inf ]);
        rotate([ 0, 0, 180 ]) translate([ -inf / 2, space / 2, thickness ])
            cube([ inf, inf, inf ]);
      }
    }
    translate([ 0, 0, thickness ]) {
      cylinder(d = id - 2 * thickness, h = inf);
    }

    // screw holes
    translate([ screw_hole_center_distance, 0, -little_more ])
        cylinder(d = screw_hole_d, h = thickness + 2 * little_more);
    translate([ -screw_hole_center_distance, 0, -little_more ])
        cylinder(d = screw_hole_d, h = thickness + 2 * little_more);
    translate(
        [ screw_hole_center_distance, 0, thickness - screw_hole_countersink_h ])
        cylinder(d = screw_hole_countersink_d,
                 h = screw_hole_countersink_h + little_more);
    translate([
      -screw_hole_center_distance, 0, thickness - screw_hole_countersink_h
    ]) cylinder(d = screw_hole_countersink_d,
                h = screw_hole_countersink_h + little_more);
  }

  // friction fit bumps

  translate([ 0, screw_hole_center_distance, thickness ])
      sphere(r = friction_bump_r);
  translate([ 0, -screw_hole_center_distance, thickness ])
      sphere(r = friction_bump_r);
}