corner(40, 1.5, 3, 20);

module corner(width, sheet, thickness, height) {
  difference() {
    triangle(width, width, height);
    translate([ thickness, thickness, thickness ]) { // slots
      cube([ sheet, width, height ]);
      cube([ width, sheet, height ]);
      triangle(sheet * 4, sheet * 4, height);
    }
    { // extra material removal
      total_thickness = 2 * thickness + sheet;
      translate([ total_thickness, total_thickness, thickness ])
          triangle(width, width, height);
    }
  }
}

module triangle(o_len, a_len, depth, center = false) {
  centroid = center ? [ -a_len / 3, -o_len / 3, -depth / 2 ] : [ 0, 0, 0 ];
  translate(centroid) linear_extrude(height = depth) {
    polygon(points = [ [ 0, 0 ], [ a_len, 0 ], [ 0, o_len ] ],
            paths = [[ 0, 1, 2 ]]);
  }
}