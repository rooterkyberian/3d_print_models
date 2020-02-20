module
lung_flat()
{
    import("c500_ice_pack.svg");
}

module
lung(height)
{
    linear_extrude(height = height)
    lung_flat();
}


w = 1.6;
h = 16;
err=0.1;

mirror([1,0,0]) {
lung(w);
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