#!/bin/bash
#FILE DESCRIPTION=======================================================
#~ Script used to write coordinates of patch centers in the given folder
#~ to the given file (in the same folder)
#~
#~ NOTES:
    #~ - must be ran from terminal with foam exted 3.1 sourced
        #~ (working only on poctar - writePatchCenterCoord was custom
        #~ compiled)
    #~ - works with reactingParcelFilmFoam of openFOAM v240+
    
#~ USAGE:
    #~ - modify and run the script

#~ TO DO:

#LICENSE================================================================
#  swritePatchCenterCoords.sh
#
#  Copyright 2015 Martin Isoz <martin@Poctar>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

foldList=(
    "Q0_1e-7.eps_1e-1_TEST"
    #~ "Q0_1e-7.eps_1e-1"
)

coordFile="coords.txt"

for i in "${foldList[@]}"
do
    #~ cd $i
    echo "cd to folder: " $i
    cd $i
    echo "writePatchCenterCoords to" $coordFile
    writePatchCenterCoords > $coordFile
    cd ..
    echo "done"
    
done
