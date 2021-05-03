$fn = 100;

spacing = 150;

module space(n) { translate([ n * spacing, 0, 0 ]) children(); }

egg_h = 100;
egg_d = 76;

base_h = 6;
base_d = egg_d;

funnel_h = 30;
funnel_inner_d = 8.6;
funnel_thickness = 1.4;
funnel_d = funnel_inner_d + 2 * funnel_thickness;
funnel_ring_h = min(funnel_h, 10);

ring_thickness = 2;
ring_tolerance = 0.6;

mold_thickness = 2;

module egg(h, d) {
  resize([ d, d, h ]) import("Dragon_Egg___Solid.stl", convexity = 3);
}

module base() { cylinder(h = base_h, d = base_d); }

module base_ring(thickness = ring_thickness, tolerance = ring_tolerance) {
  difference() {
    cylinder(h = base_h, d = base_d + 2 * thickness);
    translate([ 0, 0, -1 ]) cylinder(h = base_h * 2, d = base_d + tolerance);
  }
}

module funnel_ring(thickness = ring_thickness, tolerance = ring_tolerance) {
  difference() {
    cylinder(h = funnel_ring_h, d = funnel_d + 2 * thickness);
    translate([ 0, 0, -1 ])
        cylinder(h = funnel_ring_h * 2, d = funnel_d + tolerance);
  }
}

module inner_funnel() { cylinder(h = funnel_h * 4, d = funnel_inner_d); }

module funnel() {
  difference() {

    cylinder(h = funnel_h, d = funnel_d);
    translate([ 0, 0, -1 ]) inner_funnel();
  }
}

module whole_mold() {
  difference() {
    union() {
      hull() {
        base();
        translate([ 0, 0, -mold_thickness ]) hull()
            egg(egg_h + 2 * mold_thickness, egg_d + 2 * mold_thickness);
        translate([ 0, 0, egg_h - funnel_ring_h ]) funnel();
      }
      translate([ 0, 0, egg_h ]) funnel();
    }
    egg(egg_h, egg_d);
    translate([ 0, 0, egg_h - (funnel_h / 2) ]) inner_funnel();
  }
}

space(5) base_ring();
space(4) funnel_ring();

for (i = [0:3]) {
  space(i) {
    intersection() {
      cube([ 1000, 1000, 1000 ]);
      rotate([ 0, 0, 90 * i ]) whole_mold();
    }
  }
}