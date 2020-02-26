module
lung_flat()
{
    import("c500_ice_pack.svg");
}


w = 1.6;
h = 16;
err=0.1;
hole_r=30;
hole_space=hole_r+w;

module
lung_net()
{
    intersection()
    {
        offset(r = -w*2)
            lung_flat();
        for(i=[0:10]) {
            for(j=[0:10]) {
                translate([i*hole_space, j*hole_space, 0])
                    square(hole_r);
            }
        }
    }
}

mirror([1,0,0]) {
    linear_extrude(height = w)
        difference()
        {
            lung_flat();
            lung_net();
        }
    linear_extrude(height = 3*w)
    {
        difference()
        {
            offset(r = -w-err)
            {
                lung_flat();
            }
            offset(r = -w*2-err)
            {
                lung_flat();
            }
        }
    }
}