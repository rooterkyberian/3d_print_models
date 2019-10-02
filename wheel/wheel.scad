$fn=50;
inf=9999;

difference() {
    union() {
        cylinder(r=20, h=3);
        cylinder(r=5, h=8);
    }
    cylinder(d=0.9, h=inf);
    translate([0,0,5]) {
        rotate([90,0,0]) cylinder(d=2,h=inf);
        translate([0,-2,3]) cube([3,2,9], center=true);
    }
}

