// TV cable cover
// License: MIT
// Maciej Urbański
// rooter@kyberian.net

// dimensions
// 10.9 54; lip 12-17

inf = 9999;
$fn = 100;

module cover(w, h, d, thickness, brim) {
  difference() {
    union() {
      cube([ w, d, h ]);
      translate([ -brim, 0, -brim ])
          cube([ w + 2 * brim, thickness, h + 2 * brim ]);

      // lip
      translate([ w / 4, d, -thickness ])
          cube([ w / 2, thickness, thickness * 2 ]);
    }
    translate([ thickness, thickness, thickness ]) {
      cube([ w - 2 * thickness, d, h - 2 * thickness ]);
    }
  }
}

cover(109, 54, 12, 1, 3);