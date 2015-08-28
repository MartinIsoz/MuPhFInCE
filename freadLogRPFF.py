#!/usr/bin/python

#FILE DESCRIPTION=======================================================
#~ repeatedly read log.reactingParcelFilmFoam and stop after selected
#~ runtime
#~
#~ NOTES:
    #~ - ment for reactingParcelFilmFoam of openFOAM v240+
#~ USAGE:

#~ TO DO:
   


#LICENSE================================================================
#  freadLog.py
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

def freadLog(folder,mClockTime=15000,sleepTime=600):
    # import block------------------------------------------------------
    import os
    import time
    import io
    import sys
    # special functions-------------------------------------------------
    # custom functions--------------------------------------------------
    
    # input data--------------------------------------------------------
    cClockTime = 0
    #~ mClockTime = 250
    #~ sleepTime  = 600
    #~ folder     = 'Q0_1e-7.eps_1e-1_TEST'
    
    # listening on file part--------------------------------------------
    # skip some time for the program to start
    print 'WAITING TO START LISTENING=================\n\n'
    time.sleep(sleepTime)                                               #10 minutes is more than enough
    
    print 'Waited ' + repr(sleepTime) + ' s\n\n'
    
    print 'LISTENING ON LOG FILE======================\n\n'
        
    idStr   = 'ClockTime = '
    
    
    while cClockTime < mClockTime:
        with open('./' + folder + '/log.reactingParcelFilmFoam', 'r') as file:
            # read a list of lines into data
            data = file.readlines()                                     #not very economic to load in in
        for i in range(len(data)-1,0,-1):                               #read from the end
            fInd = data[i].find(idStr)
            if fInd>-1:
                cClockTime = int(data[i][fInd+len(idStr):len(data[i])-3])
                break
        print 'Current clockTime = ' + repr(cClockTime) + ' s, Max clockTime = ' + repr(mClockTime) + ' s'
        time.sleep(max(10,mClockTime/100))
    print 'Ending calculation\n\n'
    
    # max exec time is reached, modify controlDict----------------------
    
    # read current time (simulation)
    idStr   = 'Time = '
    
    for i in range(len(data)-1,0,-1):                                   #read from the end
            fInd = data[i].find(idStr)
            if fInd==0:                                                 #starts at the line beginning
                sTime = data[i][fInd+len(idStr):len(data[i])-1]         #read current simulation time
                break
    
    # write it to controlDict
    idStr   = 'endTime '
    
    with open('./' + folder + '/system/controlDict', 'r') as file:
        # read a list of lines into data
        data = file.readlines()
    
    for i in range(len(data)):
        fInd = data[i].find(idStr)
        if fInd==0:
            data[i] = data[i][:fInd] + idStr + '\t\t' + sTime + ';\n'
                
    with open('./' + folder + '/system/controlDict', 'w') as file:
        file.writelines( data )
        
    print 'Simulation end time changed to: endTime = ' + sTime + '\n\n'
    
    print 'DONE=======================================\n\n'
    sys.exit()
    
