#!/bin/sh

for F in `ls pixmaps/*.svg | grep gnoduino`
do
	for S in 16 22 24 32 48 64; do
		mkdir -p pixmaps/${S}x${S}
		rsvg-convert --format=png --width=${S} --height=${S} -o `echo ${F} | sed -e "s#^pixmaps/#pixmaps/${S}x${S}/#" | sed -e 's#.svg#.png#'` ${F}
	done
done

