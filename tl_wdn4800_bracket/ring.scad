module ring(r1, r2, h) {
  difference() {
    cylinder(r = r1, h = h);
    translate([ 0, 0, -1 ]) cylinder(r = r2, h = h + 2);
  }
}

ring(5, 4, 10);
