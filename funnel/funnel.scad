$fn = 100;

inf = 9999;
h = 30;
h2 = 5;
d1 = 60;
d2 = 8;
wall_thickness = 2;

module funnel(d1, d2) {
  union() {
    cylinder(h = h, d1 = d1, d2 = d2);
    translate([ 0, 0, h ]) cylinder(h = h2, d = d2);
  }
}

difference() {
  union() {
    translate([ -d1 / 2, -d1 / 2, 0 ]) cube([ d1, d1, wall_thickness ]);
    funnel(d1 = d1, d2 = d2);
  }
  funnel(d1 = d1 - wall_thickness, d2 = d2 - wall_thickness);
  translate([ d1 / 2 - 5, d1 / 2 - 5, 0 ])
      cylinder(d = 5, h = inf, center = true);
  translate([ -(d1 / 2 - 5), d1 / 2 - 5, 0 ])
      cylinder(d = 5, h = inf, center = true);
  translate([ d1 / 2 - 5, -(d1 / 2 - 5), 0 ])
      cylinder(d = 5, h = inf, center = true);
  translate([ -(d1 / 2 - 5), -(d1 / 2 - 5), 0 ])
      cylinder(d = 5, h = inf, center = true);
}
