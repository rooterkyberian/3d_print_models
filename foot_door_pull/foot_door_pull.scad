/**
 * @author Maciej Urbanski (rooter@kyberian.net)
 * @brief  Foot door pull - veritical
 * @license GPL
 * @date   May, 2020
 * @version 1.0
 *
 * Foot door pool for front gate (square bars).
 * Significantly weaker and as it would be mounted higher less practical
 * than horizontal version.
 */

gatebar_width = 25;
gatebar_depth = gatebar_width;

thickness = 5;
height = 40;

step_length = 60;
step_max_height = 3 * thickness;
step_width = 40;
step_tooth_height = thickness;
step_tooth_width = thickness;
step_tooth_spacing = thickness;

ziptie_width = 5;

$fn = 500;
TINY = 1;    // a small number, just to make to avoid renderer issues
INF = 10000; // a large number, virtually infitive

grab_w = gatebar_width + thickness;
grab_d = gatebar_depth + 2 * thickness;

union() {
  difference() {
    cube([ grab_w, grab_d, height ]);
    translate([ thickness, thickness, -TINY ])
        cube([ gatebar_width + TINY, gatebar_depth, INF ]);

    rr = gatebar_width * sqrt(2) / 2;
    translate([ 0, 0, step_max_height ]) {
      difference() {
        cube([ grab_w, grab_d, ziptie_width ]);
        translate([
          gatebar_width / 2 + thickness, gatebar_width / 2 + thickness, 0
        ]) {
          cylinder(h = ziptie_width, r = rr);
        }
      }
    }
  }

  translate([ -(step_width - gatebar_width) / 2, grab_d - thickness, 0 ]) {
    hull() {
      translate([ -thickness / 2, 0, 0 ]) cube(
          [ step_width + 2 * thickness, step_length + thickness, thickness ]);
      translate([ 0, 0, step_max_height - thickness ])
          cube([ step_width + thickness, thickness, thickness ]);
    }
    for (tooth_x = [0:step_tooth_width + step_tooth_spacing:step_width]) {
      translate([ tooth_x, step_length, thickness ]) {
        cube([ step_tooth_width, step_tooth_width, step_tooth_height ]);
      }
    }
  }
}