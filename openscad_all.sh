#!/bin/bash

set -e

DIR=$1
OPENSCAD=openscad-nightly

NPROC=$(awk '/^processor/{n+=1}END{print n}' /proc/cpuinfo)
CMD_FILE=$(mktemp --tmpdir `basename $0`.XXX)

trap "{ rm -f $CMD_FILE; }" EXIT

find $DIR -name '*.scad' | while read f;
do
	echo "$OPENSCAD -o \"${f%.scad}.png\" -o \"${f%.scad}.stl\" \"$f\"" >> $CMD_FILE;
done

cat $CMD_FILE
cat $CMD_FILE | xargs --verbose -I CMD --max-procs=$NPROC bash -c CMD
