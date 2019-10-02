/**
* @author Maciej Urbanski (rooter@kyberian.net)
* @brief  TL-WDN48000 Low profile bracket 
* @license GPL
* @date   Aug, 2013
* @version 0.3
*
* Low profile bracket for TP-Link TL-WDN4800 card. Printing with additional support highly advised due to small size and two "hanging" elements. 100% infill also wouldn't hurt.
* Holes can be slightly undersized - I figured I will have to use drills anyways, also it's easier to attach screws to smaller holes.
*/


include <bracket_base.scad>;

bracket_t = 1;
bracket_w = 18;
bracket_h = 150;
lowprofile_bracket_h = 80;
$fn = 100;

module wdn4800_bracket() {
    hw=8; //6
    hh=bracket_t+10; //+9
    ht=1.5;
    difference()
    {
        union()
        {
            lowprofile_bracket(lowprofile_bracket_h, bracket_w, bracket_t);
            translate([6.5-hw/2,0,0])
            rotate([270,0])
            {
                for(i = [0:1])
                {
                    translate([53*i,0])
                    union() {
                        translate([0,-bracket_t,0])
                        difference()
                        {
                            cube([hw,hh,ht]);
                            translate([0, 0, -ht*2])
                            linear_extrude(height=ht*5)
                            translate([hw/2, 4+ht])
                            circle(r=1, center = true);
                        }
                    }
                }
            }
        };
        //holes
        translate([0, ht, -bracket_t])
        linear_extrude(height=bracket_t*3)
        union()
        {
            translate([15, 9])
            {
                for ( i = [0:2] )
                {
                    translate([13*i,0])
                    circle(r=3, center = true);
                }
            }
            translate([52, 5])
            circle(r=2, center = true);
        }
    }
}

rotate([90,0,0])
wdn4800_bracket();
