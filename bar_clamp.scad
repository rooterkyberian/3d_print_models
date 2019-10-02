// Bar clamp
// Used for joining two rods
// GNU GPL v3
// Maciej Urbański
// rooter@kyberian.net

inf=9999;
$fn = 100;

module barclamp(rod_a_d, rod_b_d, t=2, stiff=false){
    h=rod_b_d+t*2;
    clamp_ratio=3/4;
    clamp_w=rod_a_d*clamp_ratio+t*2;
    clamp_l=rod_b_d+t*2;
    difference(){
        union(){
            cylinder(h=h, d=rod_a_d+2*t);
            translate([0, -clamp_w/2, 0]) 
                cube([rod_a_d/2+clamp_l, clamp_w, h]);
        }
        translate([0, 0, -1]) union(){
            cylinder(h=h+2, d=rod_a_d);
            if(!stiff) {
            translate([0, -rod_a_d *clamp_ratio /2, 0]) 
                cube([inf, rod_a_d *clamp_ratio, h+2]);
            }
        }
        translate([(rod_a_d+rod_b_d)/2+t, inf/2, rod_b_d/2+t])
            rotate([90, 0, 0])
                cylinder(d=rod_b_d, h=inf);
    }
}


barclamp(6, 6, 3, stiff=true);
