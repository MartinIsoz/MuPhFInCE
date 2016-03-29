#!/bin/bash

#FILE DESCRIPTION=======================================================
#
# BASH script for comparing user-selected fields
#
# ALGORITHM DESCRIPTION:
#       1. copy the fields from PARENT folder (resulting mesh)
#       2. rename all the time directories
#       3. copy the rest of the PARENT folder
#       4. mapFields (CHILD to PARENT)
#       5. perform the fields operation (subtract and mag)
#
# USAGE: modify and run the script
#
# NOTES:
#       - it is a very crude work, might be optimized and it is
#         intended to be used by an user who knows what he is doing
#       - the script WILL NOT WORK in oF 2.3.X and 2.4.X as there is
#         used a different version of mapField (which crushes)
#       - the script still has problems with comparing the fields in the
#         initial and final directories (startTime & endTime). should
#         be resolved shortly


#LICENSE================================================================
#  compFieldsV1.sh
#
#  Copyright 2015-2016 Martin Isoz <martin@Poctar>
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

#SOURCING AND STUFF=====================================================

# -- Source tutorial run functions
. $WM_PROJECT_DIR/bin/tools/RunFunctions

#SCRIPT INPUT===========================================================

# -- working directories
sourceDir1=source1                                                      #directory with the mesh to keep
sourceDir2=source2                                                      #directory with data to compare
targetDir1=target1                                                      #where to store the results

# -- fields of interest
# NOTE: At the time, I always perform copy of all the fields, which is 
#       unnecessary and dirty
fields=(alpha.liquid U)

# -- additional inputs
source1Mrk=S1                                                          #source 1 marking

#DIRECTORY COPYING======================================================
#
# GOAL: convert targetDir1 to an OpenFOAM case directory (prepare for
#       mapFields

# -- get all the time directories in the first source
cd $sourceDir1                                                          #cd to the examined directory
timeDirs=$(find -name '[0-9]*' -type d)
cd ..

# -- create (if it does not exist)
mkdir -p $targetDir1

# -- rsync the times from the first source
for i in $timeDirs; do
    rsync -r $sourceDir1/$i/ $targetDir1/$i
done

# -- rename the newly synced data
find $targetDir1/. -type f -exec mv '{}' '{}'$source1Mrk \;

# -- rsync the rest of the directories (make it a case directory)
tmList="$(echo "${timeDirs[@]}"|cut -d / -f 2-)"                        #get the list of time directories
exList="$(for i in ${tmList[@]}; do echo --exclude="\"$i\""; done)"     #create variable to exclude from rsync
endTime="$(echo "${tmList[*]}" | sort -nr | head -n1)"                  #get the latest available time

rsync -r $sourceDir1/ $targetDir1 "${exList[@]}"                        #rsync without the time directories

#MAPPING THE FIELDS=====================================================
#
# GOAL: map the fields from sourceDir2 to a targetDir1 (which has the
#       mesh of sourceDir1 and also the copied and renamed results from
#       sourceDir1

# -- map the fields from sourceDir2 to targetDir1
for i in $tmList; do
    echo processing time $i
    runApplication mapFields -case $targetDir1 -consistent -sourceTime $i $sourceDir2
    mv log.mapFields $targetDir1/log.mapFields$i
    find $targetDir1/$endTime/. -maxdepth 1 -type f ! -name "*"$source1Mrk -exec mv {} $targetDir1/$i/ \;
done
# NOTE: the behavior of mapFields is somehow wicked - the user cannot
#       specify the target time, so everything is always mapped to the
#       latest available time directory in the target folder, which is
#       not at all what we need here. hence, after each mapFields run,
#       it is necessary to move the resulting field in the proper
#       time directory

#FIELDS COMPARISON======================================================
#
# GOAL: get absolute errors on the compared fields

# -- change to the target folder
cd $targetDir1

# -- perform the calculations on specified fields
for i in "${fields[@]}"; do
    echo processing fields $i$source1Mrk $i
    foamCalc addSubtract $i$source1Mrk subtract -field $i > log.foamCalcAddSubtract$i
    foamCalc mag $i$source1Mrk\_subtract\_$i  > log.foamCalcMag$i
done

# -- create the post processing file
paraFoam -touch

# -- change back to the script folder
cd ..

exit 0
