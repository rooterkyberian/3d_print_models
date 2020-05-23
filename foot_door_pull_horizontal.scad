/**
* @author Maciej Urbanski (rooter@kyberian.net)
* @brief  Foot door pull - horizontal
* @license GPL
* @date   May, 2020
* @version 1.0
*
* Foot door pool for front gate (square bars).
*/

gatebar_width=40;
gatebar_depth=gatebar_width;

thickness=5;

step_length=60;
step_max_height=3*thickness;
step_width=40;
step_tooth_height=thickness;
step_tooth_width=thickness;
step_tooth_spacing=thickness;

ziptie_width=5;
ziptie_thickness=3;


$fn=500;
TINY=1; // a small number, just to make to avoid renderer issues
INF=10000; // a large number, virtually infitive


grab_w=gatebar_width+2*thickness;
grab_d=gatebar_depth+thickness;


difference() {
    union() {    
        difference() {
            cube([grab_w, grab_d, gatebar_width+2*thickness]);
            translate([-TINY, -TINY, thickness]) cube([INF, gatebar_width, gatebar_depth]);
        }
        
        translate([-(step_width-gatebar_width)/2, grab_d-thickness, 0]) {
            hull() {
                cube([step_width+2*thickness, step_length+thickness, thickness]);
                translate([0,0,step_max_height-thickness]) cube([step_width+thickness, thickness, thickness]);
            }
            for(tooth_x=[0:step_tooth_width+step_tooth_spacing:step_width]) {            translate([tooth_x,step_length,thickness]) {
                    cube([step_tooth_width, step_tooth_width, step_tooth_height]);
                }
            }
        }
        
    }
    
    rr=gatebar_width*sqrt(2)/2;
    translate([(grab_w-ziptie_width)/2,gatebar_width/2, gatebar_width/2+thickness]) {
        rotate([0,90,0]) {
            difference() {
                cylinder(h=ziptie_width, r=rr+ziptie_width);
                cylinder(h=ziptie_width, r=rr);
            }
        }
    }
    intersection() {
        translate([(grab_w-ziptie_width)/2,grab_d,-TINY]) cube([ziptie_width, ziptie_thickness, INF]);
        translate([(grab_w-ziptie_width)/2,gatebar_width/2, gatebar_width/2+thickness]) {
            rotate([0,90,0]) {
                cylinder(h=ziptie_width, r=rr+ziptie_width);
            }
        }
    }
}