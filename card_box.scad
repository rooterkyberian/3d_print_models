$fn=100;
/* dimensions */

card_w = 58; //60
card_h = 90;
card_z = 20;
box_thickness = 1.2;
box_neck_thickness = 0.8;


/* proportions */
box_base_to_lid = 2/3;
box_neck_to_lid = 1/3;

box_base_interior_h = card_h*box_base_to_lid;
box_lid_interior_h = card_h*1/3;
box_neck_h = box_lid_interior_h*box_neck_to_lid;

module box_base() {
    difference() {
        union() {
            cube([card_w+2*box_thickness, card_z+2*box_thickness, box_base_interior_h+2*box_thickness]);
            translate([box_thickness-box_neck_thickness,box_thickness-box_neck_thickness,box_thickness+box_base_interior_h])
                cube([card_w+2*box_neck_thickness, card_z+2*box_neck_thickness, box_neck_h+2*box_thickness]);
        }
        translate([box_thickness,box_thickness,box_thickness]) cube([card_w, card_z, card_h]);
    }
}

module box_lid() {
    difference() {
        union() {
            cube([card_w+2*box_thickness, card_z+2*box_thickness, box_lid_interior_h+2*box_thickness]);
            
        }
        translate([box_thickness,box_thickness,box_thickness])
            union() {
                cube([card_w, card_z, card_h]);
                translate([-box_neck_thickness,-box_neck_thickness,box_lid_interior_h-box_neck_h-1])
                cube([card_w+2*box_neck_thickness, card_z+2*box_neck_thickness, box_neck_h+2]);
            }
    }
}

module holes(w, h, wn=3, hn=3, t=2.4, h=100) {
    t_multiplier=2+wn-1;
    d=(w-t*t_multiplier)/wn;
    
    translate([d/2,d/2,0])
        for(h_count = [0 : hn-1]) {
            translate([0,t+h_count*(d+t),0]) {
                for(w_count = [0 : wn-1]) {
                    translate([t+w_count*(d+t),0,h/2])
                        rotate([0,0,45]) cube([(sqrt((d/2)*(d/2)*2)),(sqrt((d/2)*(d/2)*2)),h], center=true);
                        //cylinder(d=d, h=h);
                }
            }
        }
    translate([d+t/2,d+t/2,0])
        for(h_count = [0 : hn-2]) {
            translate([0,t+h_count*(d+t),0]) {
                for(w_count = [0 : wn-2]) {
                    translate([t+w_count*(d+t),0,h/2])
                        rotate([0,0,45]) cube([(sqrt((d/2)*(d/2)*2)),(sqrt((d/2)*(d/2)*2)),h], center=true);
                        //cylinder(d=d-4*t, h=h);
                }
            }
        }
}

//////////////////////////
// Put it all together //
////////////////////////

choice=0;

if(choice==1){
difference() {
    box_base();
    translate([box_thickness,50,box_thickness]) rotate([90,0,0]) holes(card_w, card_h, wn=4, hn=4);
}
}
else
{
translate([0, card_z+box_thickness*2+50, 0])
difference() {
    box_lid();
    translate([box_thickness,50,box_thickness]) rotate([90,0,0]) holes(card_w, card_h, hn=1);
}
}