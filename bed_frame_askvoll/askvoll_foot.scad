/*
 * name: Askvoll bedframe foot padding
 * author: rooter@kyberian.net
 * license: MIT
 */

module bedframe_foot(thickness = 4,
                     length = 60,
                     brim_height = 5,
                     floor_distance = 6,
                     wall_thickness = 34, )
{
    if (!floor_distance) {
        floor_distance = thickness;
    }
    difference()
    {
        cube([
            wall_thickness + 2 * thickness,
            length,
            floor_distance +
            brim_height
        ]);
        translate([ thickness, 0, floor_distance ])
        {
            cube([ wall_thickness, length, brim_height ]);
        }
        translate([ (wall_thickness + 2 * thickness) / 2, length / 2, 0 ])
        {
            cube([ 14, 40, floor_distance * 2 ], center = true);
        }
    }
}

bedframe_foot();