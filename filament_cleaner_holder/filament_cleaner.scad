$fn = 100;

filament_w = 3;
h = 15;
r = 10;
wall_w = 2;
or = r + wall_w;
oh = h + wall_w;

handle_w = 6;

inf = 1000;

difference() {
  union() {
    cylinder(h = oh, r = or);
    translate([ 0, 0, oh / 2 ]) {
      difference() {
        cube([ 2 * (or +6), handle_w, oh ], center = true);
        for (i = [ -1, 1 ]) {
          translate([ i * (or +3), 0, 0 ]) rotate([ 0, 0, 0 ])
              translate([ 0, 0, -inf / 2 ]) cylinder(h = inf, r = 3 / 2);
        }
      }
    }
  }
  translate([ 0, 0, 2 ]) { cylinder(h = oh, r = r); }
  translate([ 0, 0, -inf / 2 ]) { cylinder(h = inf, r = filament_w / 2); }
  // cut in "half"
  translate([ -inf / 2, -(handle_w / 2) - .01, oh / 2 ]) cube([ inf, 11, inf ]);
  translate([ -inf / 2, handle_w / 2, wall_w ]) cube([ inf, inf, inf ]);
}
