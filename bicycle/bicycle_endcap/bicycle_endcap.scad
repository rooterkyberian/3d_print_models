d = 22;
t = 1.5;
brim = 2;
brim_h = 4;
shape_fn = 64;
smooth_sphere = 3;
plug_top = brim * 1.5;
plug_h = 6;
plug_w = d - 2 * t;
plug_tight = 1;
plug_hole_d = plug_w * 0.5;

slot_w = plug_w * 0.2;
INF = 999;
cap_d = d + 2 * brim;

difference() {
  minkowski() {
    diff = smooth_sphere / 2;
    translate([ 0, 0, diff ]) hull() {
      cylinder(h = plug_top, d1 = d - diff, d2 = cap_d - diff, $fn = shape_fn);
      translate([ 0, 0, plug_top - diff ])
          cylinder(h = brim_h - diff, d = cap_d - diff, $fn = shape_fn);
    }
    sphere(d = smooth_sphere);
  }

  translate([ 0, 0, plug_top ]) cylinder(h = INF, d = d);
}

module slot(w) cube([ w, INF, INF ], center = true);
// plug
difference() {
  translate([ 0, 0, plug_top ]) cylinder(h = plug_h, d = plug_w + plug_tight);
  slot(slot_w);
  rotate(90) slot(slot_w);
  cylinder(h = INF, d = plug_hole_d);
}
