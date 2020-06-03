/**
* @author Maciej Urbanski (rooter@kyberian.net)
* @brief  Shower shelf
* @license GPL
* @date   June, 2020
* @version 1.0
*
*/

shelf_h=40;
shelf_w=90;
shelf_l=200;
shelf_thickness=4;
shelf_holes_d=8;
shelf_holes_space=22;

v_rod_d=22;
h_rod_d=40.5;
v_rod_wall_distance=40;

mounting_h=h_rod_d+8*shelf_thickness;
mounting_d=v_rod_d+4*shelf_thickness;


$fn=100;
SMALL=0.1;
INF=1000;

module soap(h, d, l, thickness) {
    hull() {
        translate([0,d/2,0]) cylinder(h=h, d=d);
        translate([0,l-d/2,0]) cylinder(h=h, d=d);
    }
}

module shelf_cutout() {
    difference() {
        translate([0,shelf_thickness,shelf_thickness]) soap(INF, shelf_w, shelf_l);
        translate([-INF/2,0,shelf_thickness-shelf_w/2]) cube([INF, h_rod_d/2+shelf_thickness*2, INF]);
    }
}


difference() {
    union() {
        hull() {
            cylinder(h=mounting_h, d=mounting_d);
            translate([0,0,0]) soap(shelf_h, shelf_w+2*shelf_thickness, shelf_l+2*shelf_thickness, shelf_thickness);
        }
        translate([0,0,0]) soap(shelf_h, shelf_w+2*shelf_thickness, shelf_l+2*shelf_thickness, shelf_thickness);
    }
    translate([0,0,-SMALL]) cylinder(h=INF, d=v_rod_d);
    translate([-INF/2,0,mounting_h/2]) rotate([0,90,0]) linear_extrude(height=INF) hull() {
        circle(d=h_rod_d);
        translate([0,-INF,0]) circle(d=h_rod_d);
    }
    shelf_cutout();
    intersection() {
        translate([0,0,-shelf_thickness-SMALL]) shelf_cutout();
        for(hole_x=[-shelf_w:shelf_holes_space+shelf_holes_d:shelf_l+shelf_w]) {
            for(hole_y=[0:shelf_holes_space+shelf_holes_d:shelf_l+shelf_w]) {
                translate([hole_x,hole_y,-SMALL]) cylinder(d=shelf_holes_d,h=shelf_thickness+2*SMALL);
            }
        }
    }
}