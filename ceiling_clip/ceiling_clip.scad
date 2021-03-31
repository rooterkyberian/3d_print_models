inf = 1000;
c_w = 5;

module slope(h = 10, a = 30, w = 4) {
  b = h * tan(a);
  translate([ w, 0, 0 ]) rotate([ 90, 0, -90 ]) linear_extrude(height = w)
      polygon(points = [ [ 0, 0 ], [ b, 0 ], [ 0, h ] ], paths = [[ 0, 1, 2 ]]);
}

module ceiling_clip_slides(plate_x, plate_y, t, c_t = 3, slide_w = 10,
                           slide_l = 40, r = 1) {
  union() {
    translate([ t, 0, 0 ]) cube([ slide_w * r, slide_l, t * r ]);
    translate([ plate_x - slide_w * r - t, 0, 0 ])
        cube([ slide_w * r, slide_l, t * r ]);
  }
}

module ceiling_clip_b(plate_x, plate_y, t, c_t = 2, slide_w = 10,
                      slide_l = 40) {
  union() {
    ceiling_clip_slides(plate_x, plate_y, t, c_t, slide_w, slide_l + t);
    translate([ 0, slide_l, 0 ]) difference() {
      union() {
        cube([ plate_x, t, t * 3 + c_t ]);
        translate([ 0, -c_w, t * 2 + c_t ]) cube([ plate_x, t + c_w, t ]);
        translate([ 0, -c_w, 0 ]) cube([ plate_x, t + c_w, 2 * t ]);
      }
      // FIXME check if this hole meets slides
      translate([ plate_x / 2, t / 2, 0 ]) rotate([ 90, 0, 0 ])
          cylinder(r = t * 2 + c_t, h = inf, center = true);
    }
  }
}

module ceiling_clip_a(plate_x, plate_y, t, c_t = 2, slide_w = 10,
                      slide_l = 40) {
  slide_hole_r = 1.1;
  slide_box_w = slide_w * slide_hole_r + 2 * t;
  difference() {
    union() {
      // base
      cube([ plate_x, plate_y, t ]);
      // grip
      translate([ 0, plate_y / 2 - c_w - t, 0 ]) union() {
        slope(a = 60, h = t * 4 + c_t, w = plate_x);
        cube([ plate_x, t, t * 3 + c_t ]);
        translate([ 0, 0, t * 3 + c_t ]) cube([ plate_x, t + c_w, t ]);
      }
      // slide box
      translate([ 0, 0, t ]) cube([ slide_box_w, plate_y / 2, t * 2 ]);
      translate([ plate_x - slide_box_w, 0, t ])
          cube([ slide_box_w, plate_y / 2, t * 2 ]);
    }
    // slide holes
    translate([ 0, -1, t ]) ceiling_clip_slides(
        plate_x, plate_y, t, c_t, slide_w, slide_l = plate_x, r = slide_hole_r);
    translate([ -inf / 2, -inf, -inf / 2 ]) cube([ inf, inf, inf ]);
  }
}

/*
rotate([-90,0,0])
translate([0,0,2]) ceiling_clip_b(50, 50, 2);
*/
union() {
  translate([ 0, 0, 0 ]) rotate([ 90, 0, 0 ]) ceiling_clip_a(50, 50, 2);
  translate([ 15, -10, 0 ]) cube([ 20, 20, 1.05 ]);
}
// ceiling_clip_a(50, 50, 2);
// translate([0, $t*50, 2]) ceiling_clip_b(50, 50, 2, slide_l=40);
