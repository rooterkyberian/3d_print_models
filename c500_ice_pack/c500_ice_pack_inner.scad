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


w = 2;
h = 16;
err=0.1;

mirror([1,0,0]) {
lung(w);
linear_extrude(height = h-w)
{
    difference()
    {
        offset(r = -w/2-err)
        {
            lung_flat();
        }
        offset(r = -w-err)
        {
            lung_flat();
        }
    }
}
}