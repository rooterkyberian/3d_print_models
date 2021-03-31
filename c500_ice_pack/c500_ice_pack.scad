module lung_flat() { import("c500_ice_pack.svg"); }

module lung(height) { linear_extrude(height = height) lung_flat(); }

w = 1.6;
h = 16;

lung(w);
linear_extrude(height = h - w) {
  difference() {
    offset(r = 0) { lung_flat(); }
    offset(r = -w) { lung_flat(); }
  }
}