#!/bin/bash

export DIR=$1
export OPENSCAD=openscad-nightly

find $DIR -name '*.scad' | while read f;
do
	$OPENSCAD -o ${f%.scad}.stl $f;
done
