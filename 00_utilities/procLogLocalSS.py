#!/usr/bin/python

#FILE DESCRIPTION=======================================================
#
# Simple python script to see the residuals evolution and other
# simulation characteristics of the steady state OpenFOAM runs
#
# Required:
#   - file log.*Foam
#   - file log.blockMesh or log.snappyHexMesh or direct specification
#     of the number of the cells in the mesh

#USAGE==================================================================
#  1. Copy the script to a clean folder (or specify checkDir)
#  2. Run the script

#LICENSE================================================================
#  procLog.py
#
#  Copyright 2016 Martin Isoz <martin@Poctar>
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

#IMPORT BLOCK===========================================================
# -- communication with the remote server
import os
# -- plot updating
import time
# -- math and other operations on the data
import math
import glob
import sys
import numpy as np
import re                                                               #regexp
# -- plotting
import matplotlib.pyplot as plt
import matplotlib
import textwrap
from itertools import cycle,chain

#CUSTOM FUNCTIONS=======================================================
# A. auxiliary visualization functions----------------------------------
def createCyclers():
    """ function to create cyclers for plot styling in 1 line"""
    # -- prepare the list entries
    lines           = ['-','--','-.',':']
    markers         = ['o','v','h','d','s','^']
    colors          = [
                        'dodgerblue',
                        'limegreen',
                        'darkmagenta',
                        'saddlebrown',
                        'firebrick',
                        'teal',
                        'gold',
                      ]
    return cycle(lines),cycle(markers),cycle(colors)

#INPUT VARIABLES========================================================
# -- for which variables I want to see the residuals
#~ varInt  = ['alpha.liquid','p_rgh']
#~ varInt  = ['p_rgh']
varInt  = [
            'Ux','Uy','Uz',
            'p',
            'k','omega',
]

# -- how many last iterations do I want to see?
# TBD

# -- which residuals I want to get (final or initial)
finRes  = False

# -- which file to get
fileList= ['log.blockMesh', 'log.simpleFoam']

# -- periodic updating of the figures
updatePl= False                                                          #update the plot?
updInt  = 20                                                            #update interval in seconds

# -- graphical output parameters
eMS     = 10                                                            #marker size to show the current timestep

#OUTPUT VARIABLE========================================================
fileNm = 'simAnalysisData'

#DO NOT MODIFY (PREFERABLY)=============================================
strAux  = [
             'echo "$(head /proc/cpuinfo | grep ',
              "'model name')",
              '" | awk -F ": " ',
              "'{print $2}'",
          ]

sTitle = os.popen(strAux[0] + strAux[1] + strAux[2] + strAux[3]).read()

sTitle = sTitle[:-1]                                                    #cut out the last (newLine) character

# -- local location
checkDir= os.getcwd() + '/'                                             #get current directory


# -- figure window parameters
fig = plt.figure(num=None, figsize=(20, 12), dpi=80, facecolor='w', edgecolor='k')
plt.show(block=False)
# -- colors for plots with unknown number of lines
plotCols = [np.random.rand(3,1) for i in range(len(varInt))]

font = {
        #~ 'family' : 'normal',
        #~ 'weight' : 'normal',
        'size'   : 22
}

matplotlib.rc('font', **font)


#PROGRAM ITSELF=========================================================
while True:    
    #PROCESS OTHER LOG FILES (MESH CHARACTERISTICS & OTHER)=============
    with open(checkDir + fileList[0], 'r') as file:
        # read a list of lines into data
        data = file.readlines()
        
    idStr = ['nCells: ']                                                #get number of cells in the mesh
    
    for j in range(len(idStr)):
        for i in range(len(data)):
            fInd = data[i].find(idStr[j])
            if fInd>=0:
                nCells = round(float(data[i][fInd+len(idStr[j])::])/1e6,1)
                break
    
    
    #LOAD THE FILE INTO MEMORY==========================================
    with open(checkDir + fileList[1], 'r') as file:
        # read a list of lines into data
        data = file.readlines()
    
    #GET NUMBER OF CORES USED (AND POSSIBLY OTHER DESCRIPTION)==========
    idStr = [
                'nProcs : ',
                'Date   : ',
                'Time   : ',
                'Case   : ',
                'Exec   : ',
                'Build  : ',            
            ]
    
    out = []
    
    for j in range(len(idStr)):
        for i in range(len(data)):
            fInd = data[i].find(idStr[j])
            if fInd==0:
                out.append(data[i][fInd+len(idStr[j])::])
                break
                
    nProcs = int(out[0])                                                #get number of cores
    Date,Time,Case,Exec,Build = out[1::]                                #get start time and date and case
    Date,Time,Case,Exec,Build = Date[0:-1],Time[0:-1],Case[0:-1],Exec[0:-1],Build[0:-1]
    
    Case   = Case.split('/')                                            #extract relevant data from the case
    Case   = Case[-1]
    
    ttlStr = ("%s, %d cores, %.1fMM cells, case: %s, "%(sTitle, nProcs, nCells, Case) + 
                 "solver: %s, version: %s"%(Exec, Build))
    plt.suptitle("\n".join(textwrap.wrap(ttlStr, 100)),
                 fontsize=24)
    
    
    #PLOT TIMESTEPEVOLUTION=============================================
    # -- not applicable for the steady state simulations
    
    #PLOT THE RESIDUALS=================================================
    # TBD: modification for being able to choose how many timesteps I
    #      want to see
    partData = data
            
    #~ partData.reverse()                                                  #flip the list
    
    
    idStr = ['Solving for %s'%varName for varName in varInt]            #in which variables am I interested
    
    vec   = [[] for i in range(len(varInt))]                            #reziduals
    lVarInt = len(vec)
    
    # Note: I suspect, that the bellow is not exactly pretty (but it works)
    updLst = [False]*lVarInt                                            #create list which tells me, if the variables were updated
                
    for i in range(len(partData)):                                      #go through the partData
        if partData[i].find('Time = ') == 0:                            #if I reach a new iteration
            k = 0
            cVecLen = len(vec[0])                                       #get current veclength
            aVecLen = cVecLen                                           #auxiliary variable
            while any(itm == False for itm in updLst):                  #if any of the variables is still not updated
                for j in range(len(idStr)):                             #go throught the variables of interest
                    fInd = partData[i+k].find(idStr[j])
                    if fInd>-1 and not updLst[j]:
                        auxStr = partData[i+k][fInd::].split('residual = ')       #lets split the rest using residual. should result in 3 substrings (2 occurences of the splitting string)
                        if not finRes:
                            vec[j].append(float(auxStr[1].split(',')[0]))       #process the first occurence
                        else:
                            vec[j].append(float(auxStr[2].split(',')[0]))       #process the last occurence
                        updLst[j] = True
                k += 1
            updLst = [False]*lVarInt                                #reset the updates
                
    
    host = plt.subplot2grid((1,1),(0,0), colspan = 1)
    plt.cla()
    plt.xlim([0,max([len(vv) for vv in vec])])
    #~ plt.grid(True, which='major')
    mLen = max([len(v) for v in vec])                                   #maximal vector length
    linecycler,markercycler,colorcycler=createCyclers() #restart the cyclers
    for i in range(len(varInt)):
        cLen = len(vec[i])
        host.semilogy(np.linspace(0,mLen,cLen),vec[i],'-',c=next(colorcycler),label=varInt[i],lw=3)
    host.set_ylabel('Reziduals')
    host.set_xlabel('Number of iterations')
    host.set_ylim([10**(math.floor(math.log10(min(min(vec))))),1])
    host.legend(bbox_to_anchor=(0.7, 0.95), loc=2, borderaxespad=0.)
    
    #PLOT CALCULATION TIME==============================================
    idStr = [
             'ExecutionTime = ',
            ] 
    
    vec   = [[0.0],[0.0],[0]]
        
    for j in range(len(idStr)):
        for i in range(len(data)):
            fInd = data[i].find(idStr[j])
            if fInd>-1:
                curTime = data[i].split(' ')                            #split the relevant line by spaces
                curTime = float(curTime[2])                             #hardcoded position (solver specific)
                vec[j].append(curTime)                                  #current execution time
                vec[j+1].append(curTime-vec[j][-2])                     #current timestep difference
                vec[j+2].append(vec[j+2][-1]+1)                         #timestep number
           
    meanVal = np.mean(vec[1])                                           #get mean value
    vec.append([absVal/meanVal for absVal in vec[1]])
        
    hExecTime = [execTime/3600 for execTime in vec[0]] 
    
    par  = host.twinx()
    par.fill_between(
        np.linspace(0,len(vec[1]),len(vec[1])),0,vec[1],
        color = next(colorcycler),
        alpha = 0.3,
        zorder = -1,
    )
    par.set_ylabel('Computation time / time step, [s]')
    par.set_ylim([min(vec[1])*0.9,max(vec[1])*1.1])
    
    plt.axis('tight')
    
    #PLOT COURANT AND INTERFACE COURANT NUMBERS=========================
    # -- not applicable for the steady state simulations
    
    #PLOT RESIDUALS OVER LAST M TIME STEPS==============================
    # -- not applicable for the steady state simulations
    
    #SAVE THE RESULTING FIGURE AND UPDATE GRAPHS========================
    # -- draw the figure
    plt.tight_layout(rect=[0, 0.03, 1, 0.90])
    plt.savefig('runAnalysis.png', dpi=160)
    plt.draw()    
    
    if not updatePl:
        break

    time.sleep(updInt)
    
plt.show()
