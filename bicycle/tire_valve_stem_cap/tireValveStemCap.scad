// Tire valve stem cap
// original: https://www.thingiverse.com/thing:34517
// license: https://creativecommons.org/licenses/by-sa/3.0/

external_d = 11.2;
outer_fn = 10;
thread_h = 11;
inner_d_high = 7.95;
inner_d_low = 7.98;
$fn = 100;

difference() {
  union() {
    cylinder(thread_h, d = external_d, $fn = outer_fn);
    translate([ 0, 0, thread_h ]) sphere(d = external_d, $fn = outer_fn);
  }
  union() {
    translate([ 0, 0, -1 ])
        cylinder(thread_h + 1.1, d1 = inner_d_low, d2 = inner_d_high);
    translate([ -5, -5, thread_h + external_d / 4 ]) cube([ 10, 10, 3 ]);
    translate([ 0, 0, 9 ]) sphere(3, $fs = .25);
  }
}
