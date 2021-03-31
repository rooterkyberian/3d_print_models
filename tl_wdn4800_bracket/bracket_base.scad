/**
 * @author Maciej Urbanski (rooter@kyberian.net)
 * @brief  PC bracket base modules
 * @license GPL
 * @date   Aug, 2013
 * @version 0.1
 *
 */

bracket_t = 1;
highprofile_bracket_h = 120;
lowprofile_bracket_h = 80;

module bracket_handle(w, t) {
  bw = 11;
  hole_w = 4;
  linear_extrude(height = t) union() {
    difference() {
      square([ bw + t, w ]);
      translate([ 6 + t, w - 5 ]) {
        circle(r = hole_w / 2);
        translate([ -hole_w / 2, 0, 0 ]) { square([ hole_w, 1000 ]); }
      }
    }
  }
}

module bracket_base(h, w, t) {
  s1 = 4;
  s2 = 7;
  main_part_h = h - (s1 + s2);
  s3 = (w - 10) / 2;
  linear_extrude(height = t)
      polygon(points =
                  [
                    [ 0, 0 ], [ 0, w ], [ main_part_h, 0 ], [ main_part_h, w ],
                    [ main_part_h + s1, s1 ], [ main_part_h + s1, w - s1 ],
                    [ h, s3 ], [ h, w - s3 ]
                  ],
              paths = [[ 0, 1, 3, 5, 7, 6, 4, 2 ]]);
}

module lowprofile_bracket(h, w, t) {
  union() {
    // lower half
    bracket_base(h, w, t);
    // handle
    translate([ t, 4, 0 ]) rotate([ 0, 270 ]) bracket_handle(w, t);
  }
}

module bracket(h, w, t) {
  handle_m = 3;
  cut_h = 5;
  union() {
    // lower half
    difference() {
      bracket_base(h + t, w, t);
      translate([ -1, w - handle_m, -t ])
          cube([ 1 + cut_h, 1 + handle_m, 3 * t ]);
    }
    // handle
    translate([ 0, w - handle_m, 0 ]) rotate([ 180, 270 ]) bracket_handle(w, t);
  }
}
