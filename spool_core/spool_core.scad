inf=500;
$fn=100;

module spool_core(rods=3, rod_d=6, t=4, bearing_D=19) {
    nut_f=10;
    nut_h=5.2;
    arm_l=20;
    w=nut_f+2*t;
    h=rod_d+2*t;
    union(){
        //arms
        for(i=[0:rods]) {
            rotate([0,0,360/rods*i]){
                difference(){
                    translate([bearing_D/2,-w/2,0]){
                        cube([t+arm_l, w, h]);
                    }
                    translate([bearing_D/2+t+arm_l/2-nut_h/2,-nut_f/2,-1]){
                        cube([nut_h,nut_f,h+2]);
                    }
                    translate([bearing_D/2+t,0,h/2]) rotate([0,90,0]){
                        cylinder(d=rod_d, h=inf);
                    }
                }
            }
        }
        //bearing holder
        difference(){
            union(){
                cylinder(d=bearing_D+2*t, h=h);
                cylinder(d=bearing_D+2*t, h=t);
            }
            //bearing hole
            translate([0,0,-1])
                cylinder(d=bearing_D-t, h=h+2);
            translate([0,0,t]){
                cylinder(d=bearing_D, h=h);
                cylinder(d1=bearing_D+1, d2=bearing_D, h=h-t);
            }
        }
    }
}

spool_core();
