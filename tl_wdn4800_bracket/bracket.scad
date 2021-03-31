bracket_t = 1;

bracket_w = 18;
bracket_h = 150;
lowprofile_bracket_h = 80;

module bracket_handle(w, t) {
  bw = 12;
  linear_extrude(height = bracket_t) union() {
    difference() {
      square([ bw, w ]);
      translate([ 7, w - 5 ]) {
        circle(r = 2);
        translate([ -2, 0, 0 ]) { square([ 4, 1000 ]); }
      }
    }
  }
}

module bracket_base(h, w, t) {
  s1 = 4;
  s2 = 7;
  main_part_h = h - (s1 + s2);
  s3 = (w - 10) / 2;
  linear_extrude(height = t)
      polygon(points =
                  [
                    [ 0, 0 ], [ 0, w ], [ main_part_h, 0 ], [ main_part_h, w ],
                    [ main_part_h + s1, s1 ], [ main_part_h + s1, w - s1 ],
                    [ h, s3 ], [ h, w - s3 ]
                  ],
              paths = [[ 0, 1, 3, 5, 7, 6, 4, 2 ]]);
}

module bracket(h, w, t) {
  union() {
    // lower half
    bracket_base(h, w, t);
    // handle
    translate([ t, 4, 0 ]) rotate([ 0, 270 ]) bracket_handle(w, t);
  }
}

module wdn4800_bracket() {
  difference() {
    union() {
      bracket(lowprofile_bracket_h, bracket_w, bracket_t);
      translate([ 5, 0, 0 ]) rotate([ 270, 0 ]) {
        for (i = [0:1]) {
          translate([ 52 * i, 0 ]) union() {
            translate([ 0, -bracket_t, 0 ]) difference() {
              cube([ 6, 10, bracket_t * 2 ]);
              translate([ 0, 0, -bracket_t * 2 ])
                  linear_extrude(height = bracket_t * 2 * 3) translate([ 3, 7 ])
                      circle(r = 1, center = true, $fn = 10);
            }
          }
        }
      }
    };
    translate([ 0, bracket_t, -bracket_t ])
        linear_extrude(height = bracket_t * 3) union() {
      translate([ 15, bracket_w / 2 ]) {
        for (i = [0:2]) {
          translate([ 13 * i, 0 ]) circle(r = 3.5, center = true);
        }
      }
      translate([ 52, 5 ]) circle(r = 1.5, center = true, $fn = 10);
    }
  }
}

wdn4800_bracket();
