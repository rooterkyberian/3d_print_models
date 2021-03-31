/**
 * @author Maciej Urbanski (rooter@kyberian.net)
 * @brief  TL-WDN48000 Low profile bracket
 * @license GPL
 * @date   Aug, 2013
 * @version 0.3
 *
 * Low profile bracket for TP-Link TL-WDN4800 card. Printing with additional
 * support highly advised due to small size and two "hanging" elements. 100%
 * infill also wouldn't hurt. Holes can be slightly undersized - I figured I
 * will have to use drills anyways, also it's easier to attach screws to smaller
 * holes.
 */

include<bracket_base.scad>;

bracket_t = 1;
bracket_w = 18;
bracket_h = 121;

ant_hole_r = 3.5;
ant_hole_h = 5.5 + ant_hole_r;
led_hole_r = 3;
led_hole_h = 5.7 + led_hole_r;
screw_hole_r = 1;
screw_hole_h = 7;
screw_spacing = 54;

ant_spacing = 12;

handles_h = 3;

apart = 54;
$fn = 100;

module dwa_bracket() {
  card_m = 10;
  hw = 8;              // 6
  hh = bracket_t + 11; //+9
  ht = 3;
  difference() {
    union() {
      bracket(highprofile_bracket_h, bracket_w, bracket_t);
      translate([ card_m, handles_h, 0 ]) rotate([ 270, 0 ]) {
        for (i = [0:1]) {
          translate([ screw_spacing * i, -bracket_t, 0 ]) difference() {
            cube([ hw, hh, ht ]);

            translate([ 0, 0, -ht * 2 ]) linear_extrude(height = ht * 5)
                translate([ hw / 2, screw_hole_h + screw_hole_r + bracket_t ])
                    circle(r = screw_hole_r, center = true);
          }
        }
      }
    }
    // holes
    translate([ card_m, 0, -bracket_t ])
        linear_extrude(height = bracket_t * 3) union() {
      translate([ 13, ant_hole_h ]) {
        for (i = [0:2]) {
          translate([ ant_spacing * i, 0 ])
              circle(r = ant_hole_r, center = true);
        }
      }
      translate([ 48, led_hole_h ]) circle(r = led_hole_r, center = true);
    }
  }
}

rotate([ 90, 0, 0 ]) dwa_bracket();
