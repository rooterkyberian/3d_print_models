// Loose Bar clamp
// Used for loose joining two rods
// GNU GPL v3
// Maciej Urbański
// rooter@kyberian.net

inf=9999;
$fn = 100;

module loose_barclamp(rod_a_d, rod_b_d, width=2, h=20){

    difference(){
        hull(){
            cylinder(h = width+rod_b_d/2, r=rod_a_d/2+width);
            translate([(rod_b_d+width)/2, -(rod_b_d+width)/2, 0]) 
                cube([rod_b_d+width, rod_b_d+width, h]);

        }

        cylinder(h = inf, d=rod_a_d, $fn = 20);
        translate([rod_b_d+width, 0, rod_b_d/2+width]) 
            union() {
                translate([0, inf/2, 0]) rotate([90, 0, 0]) cylinder(d=rod_b_d, h=inf);
                translate([-rod_b_d/2,-inf/2,0]) cube([rod_b_d, inf, inf]);
            }

    }
}


difference(){
    loose_barclamp(6, 6, 3, 15);
    translate([0,0,7]) cylinder(h=10, d=11.5, $fn=6);
}
