#!/usr/bin/python

#FILE DESCRIPTION=======================================================
#~ Simple python script to visualize the simulation run

#~ Goal is to check on how is Altix performing. Script goes through
#~ log.interFoam and log.blockMesh and uses those data to get a notion on
#~ simulation run (during runtime)

#~ There is a possibility to periodically update the graphs
#~ I do not use very efficient algorithm - all is recalculated as the
#~ variables are rewritten (dirty but working, space for an improvment)

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

#CUSTOM FUNCTIONS=======================================================
def avServers(rName):
    return {
        'Altix' : [#Altix UV 2000 at UCT prague
                    'altix.vscht.cz',
                    'isozm',
                    ['/scratch/','/'],
                    'Altix UV 2000',                        
                  ],
        'Poctar': [#my personnal computer at UCT prague
                    '413-C407-Poctar.vscht.cz',
                    'martin',
                    ['/media/','/Data_2/05_TextPlate/10_noTextureV2/'],
                    #~ ['/media/','/Data_2/05_TextPlate/40_pyrTextureV2/'],
                    #~ ['/media/','/Data_2/05_TextPlate/50_transTextureV2/'],
                    #~ ['/media/','/Data_2/05_TextPlate/60_longTextureV2/'],
                    'Intel Xeon E3',                        
                  ],
    }.get(rName,'Altix')

#INPUT VARIABLES========================================================
# -- for which variables I want to see the residuals
#~ varInt  = ['alpha.liquid','p_rgh']
varInt  = ['p_rgh']

# -- specification of how many last timesteps I want to examine
nRezSt  = 2                                                             #number of timesteps to show reziduals for (keep low, there is alway +- 5 points for each timestep)
nPimpIt = 50                                                            #number of timesteps to show number of PIMPLE iterations for (if a very high number is specified, all the simulation timesteps will be shown)

# -- checked case
#~ caseName= 'iF_Re30.0_60.0_H2OCk_SMV2_CN_linUW_intComp'
#~ caseName= 'iF_Re30.0_60.0_H2OCk_SMV2_UW'
#~ caseName= 'iF_Re30.0_60.0_H2OCk_PTV2_INIT'
#~ caseName= 'iF_Re30.0_60.0_H2OCk_TTV2_MAPPED'
#~ caseName= 'iF_Re20.0_60.0_H2OCk_PT'
caseName= 'iF_Re30.0_60.0_H2OCk_SMV2_VCell0.009mm3'
#~ caseName= 'iF_Re30.0_60.0_H2OCk_SMV2_VCell0.014mm3'
#~ caseName= 'iF_Re30.0_60.0_H2OCk_SMV2_VCell0.020mm3'
#~ caseName= 'iF_Re30.0_60.0_H2OCk_SMV2_VCell0.027mm3'
#~ caseName= 'iF_Re30.0_60.0_H2OCk_SMV2_VCell0.035mm3'
#~ caseName= 'iF_Re30.0_60.0_H2OCk_SMV2_VCell0.079mm3'
#~ caseName= 'iF_Re30.0_60.0_H2OCk_SMV2_VCell0.118mm3'
#~ caseName= 'iF_Re30.0_60.0_H2OCk_SMV2_VCell0.210mm3'
#~ caseName= 'iF_Re30.0_60.0_H2OCk_PTV2_VCell0.020mm3'
#~ caseName= 'iF_Re30.0_60.0_H2OCk_PTV2_VCell0.035mm3'
#~ caseName= 'iF_Re30.0_60.0_H2OCk_PTV2_VCell0.079mm3'
#~ caseName= 'iF_Re30.0_60.0_H2OCk_TTV2_VCell0.020mm3'
#~ caseName= 'iF_Re30.0_60.0_H2OCk_TTV2_VCell0.035mm3'
#~ caseName= 'iF_Re30.0_60.0_H2OCk_TTV2_VCell0.079mm3'
#~ caseName= 'iF_Re240.0_60.0_H2OCk_PSV3_INIT'

# -- remote server
rName   = 'Altix'
#~ rName   = 'Poctar'

rServer,rUser,caseDir,sTitle = avServers(rName)                         #get server description
caseDir = caseDir[0] + rUser + caseDir[1] + caseName + '/'              #set proper caseDir

# -- local location
checkDir= os.getcwd() + '/'                                             #get current directory

# -- which file to get
fileList= ['log.blockMesh', 'log.interFoam']

# -- periodic updating of the figures
updatePl= True                                                          #update the plot?
updInt  = 10                                                            #update interval in seconds

# -- graphical output parameters
eMS     = 10                                                            #marker size to show the current timestep

#OUTPUT VARIABLE========================================================
fileNm = 'simAnalysisData'
outVar = []

#DO NOT MODIFY (PREFERABLY)=============================================
# -- figure window parameters
plt.figure(num=None, figsize=(20, 12), dpi=80, facecolor='w', edgecolor='k')
plt.show(block=False)
# -- colors for plots with unknown number of lines
plotCols = [np.random.rand(3,1) for i in range(len(varInt))]


#PROGRAM ITSELF=========================================================
while True:
    #GET THE CURRENT DATA===============================================
    for rFile in fileList:
        os.system('rsync -v "%s:%s" "%s"' % (rUser + '@' + rServer,
                                        caseDir + rFile,
                                        checkDir) )
    
    #PROCESS OTHER LOG FILES (MESH CHARACTERISTICS & OTHER)=============
    with open(checkDir + 'log.blockMesh', 'r') as file:
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
    with open(checkDir + 'log.interFoam', 'r') as file:
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
    
    plt.suptitle("%s, %d cores, %.1fMM cells, case: %s,\n"%(sTitle, nProcs, nCells, Case) + 
                 "solver: %s, version: %s\n"%(Exec, Build),
                 fontsize=24)
    
    
    #PLOT TIMESTEPEVOLUTION=============================================
    idStr = ['deltaT = ',
             'Time = ',
            ] 
    
    vec   = [[],[]]
        
    for j in range(len(idStr)):
        for i in range(len(data)):
            fInd = data[i].find(idStr[j])
            if fInd==0:
                vec[j].append(float(data[i][fInd+len(idStr[j])::]))
                
    outVar.append(vec)
                
    plt.subplot(2,3,1)
    plt.cla()
    plt.semilogy(vec[1],vec[0], 'g^')
    plt.title('Timestep evolution')
    plt.ylabel('Adaptive timestep [s]')
    plt.xlabel('Simulation time [s]')
    plt.xlim([min(vec[1]),max(vec[1])])
    plt.ylim([1e-6,max([max(vec[0]),1e-4])])
    plt.grid(True, which='major')
    plt.grid(True, which='minor')
    plt.draw()
    
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
    
    outVar.append(vec)
    
    hExecTime = [execTime/3600 for execTime in vec[0]] 
    
    plt.subplot(2,3,2)
    plt.cla()
    plt.plot(hExecTime,vec[1], 'bo')
    for i in range(1,1+int(math.floor(hExecTime[-1]/24))):
        plt.plot([24*i, 24*i], [min(vec[1])*0.9,max(vec[1])*1.1], 'k-.')
        plt.text(24*i-max(hExecTime)/20,max(vec[1])*1.0,'Day %i'%i,bbox={'facecolor':'blue', 'alpha':0.5, 'pad':10}, rotation='vertical')
    plt.title('Timestep computation time during simulation')
    plt.ylabel('Computation time / time step [s]')
    plt.xlabel('Execution time [h], started on %s, %s'%(Date, Time))
    plt.xlim([min(hExecTime),max(hExecTime)])
    plt.ylim([min(vec[1])*0.9,max(vec[1])*1.1])
    plt.grid(True)
    plt.draw()
    
    #PLOT COURANT AND INTERFACE COURANT NUMBERS=========================
    idStr = [
                'Courant Number',
                'Interface Courant Number',
            ]
            
    vec = [[],[],[],[]]
    
    for j in range(len(idStr)):
        for i in range(len(data)):
            fInd = data[i].find(idStr[j])
            if fInd==0:
                curVals = data[i][fInd+len(idStr[j])::].split(' ')
                vec[2*j].append(float(curVals[2]))
                vec[2*j+1].append(float(curVals[4]))
                
    outVar.append(vec)
    
    nElems = [len(vec[i]) for i in range(len(vec))]
    nElems = min(min(nElems),len(outVar[1][2]))
    
    plt.subplot2grid((2,3), (1,0), colspan=2)
    plt.cla()
    plt.semilogy(outVar[1][2][:nElems],vec[0][:nElems], 'co',label='Co (mean)')
    plt.semilogy(outVar[1][2][:nElems],vec[1][:nElems], 'cd',label='Co (max)')
    plt.semilogy(outVar[1][2][:nElems],vec[2][:nElems], 'mo',label='Co_I (mean)')
    plt.semilogy(outVar[1][2][:nElems],vec[3][:nElems], 'md',label='Co_I (max)')
    plt.legend(bbox_to_anchor=(0.7, 0.3), loc=2, borderaxespad=0.)
    plt.title('Courant number evolution during simulation')
    plt.ylabel('Courant number [--]')
    plt.xlabel('Simulation step [--]')
    plt.xlim([min(outVar[1][2]),max(outVar[1][2])])
    plt.grid(True)
    plt.draw()
    #~ 
    #PLOT RESIDUALS OVER LAST N TIME STEPS==============================
    # -- get only the last N PIMPLE iteration
    partData = []
    nCntr    = 0
    for i in range(len(data)-1,0,-1):
        fInd = data[i].find('PIMPLE: iteration 1')
        if fInd==-1:
            partData.append(data[i])
        else:
            nCntr = nCntr + 1
            if nCntr == nRezSt:
                break
            
    partData.reverse()                                                  #flip the list
    
    
    idStr = ['Solving for %s'%varName for varName in varInt]            #in which variables am I interested
    
    vec   = [[]]*len(varInt)                                            #reziduals
            
    for i in range(len(partData)):                                      #go through the partData
        for j in range(len(idStr)):                                     #go throught the variables of interest
            fInd = partData[i].find(idStr[j])
            if fInd>-1:
                auxStr = partData[i][fInd::].split('residual = ')                 #lets split the rest using residual. should result in 3 substrings (2 occurences of the splitting string)
                vec[j].append(float(auxStr[1].split(',')[0]))        #process both the occurences
                vec[j].append(float(auxStr[2].split(',')[0]))
                
                
    plt.subplot(2,3,3)
    plt.cla()                                                           #clear the current axis
    # time.sleep(0.5)
    for i in range(len(varInt)):
        plt.semilogy(vec[i],'s-',c=plotCols[i],label=varInt[i])
    plt.title('Reziduals evolution')
    plt.ylabel('Reziduals')
    plt.xlabel('last %d PIMPLE iterations'%nCntr)
    plt.xlim([0,len(vec[0])])
    plt.ylim([1e-8,1])
    plt.grid(True, which='major')
    plt.legend(bbox_to_anchor=(0.7, 0.95), loc=2, borderaxespad=0.)
    plt.draw()
    
    #PLOT RESIDUALS OVER LAST M TIME STEPS==============================
    # -- get only the last M PIMPLE iteration
    partData = []
    nCntr    = 0
    for i in range(len(data)-1,0,-1):
        fInd = data[i].find('PIMPLE: iteration 1')
        if fInd==-1:
            partData.append(data[i])
        else:
            nCntr = nCntr + 1
            if nCntr == nPimpIt:
                break
            
    partData.reverse()                                                  #flip the list
    
    idStr = ['PIMPLE: converged in']
    
    vec   = []
    
    for i in range(len(partData)):                                      #go through the partData
        for j in range(len(idStr)):                                     #go throught the variables of interest
            fInd = partData[i].find(idStr[j])
            if fInd>-1:#well, not exactly top notch but does the trick
                vec.append(int(re.findall('\d+', partData[i][fInd+len(idStr[j])::])[0]))    
    
    plt.subplot(2,3,6)
    plt.cla()
    if not vec:
        plt.text(0.17,0.5,'Solver NOT operating in PIMPLE mode')
    else:
        # time.sleep(0.5)
        plt.plot(vec,'d',c='darkgoldenrod')
        plt.title('Number of PIMPLE iterations')
        plt.ylabel('PIMPLE iterations')
        plt.xlabel('last %d timesteps'%nCntr)
        plt.xlim([0,len(vec)])
        plt.ylim([0,min(max(vec)+1,50)])
        plt.grid(True, which='major')
    
    plt.draw()

    
    
    #SAVE THE RESULTING FIGURE AND UPDATE GRAPHS========================
    # -- draw the figure
    plt.savefig('runAnalysis.png', dpi=160)
    plt.draw()    
    
    if not updatePl:
        break

    time.sleep(updInt)
    
plt.show()
    
#PREPARE AND WRITE THE OUTPUT FILE (FOR PROPER PLOTING)=================
#~ wrList = [#variable to be written to the file
            #~ 'simTime'       + '\t' +    #outVar[0][1]
            #~ 'timeStep'      + '\t' +    #outVar[0][0]
            #~ 'execTime'      + '\t' +    #outVar[1][0]
            #~ 'timeStepTime'  + '\t' +    #outVar[1][1]
            #~ 'simStep'       + '\t' +    #outVar[1][2] !!INT!!
            #~ 'avgCo'         + '\t' +    #outVar[2][0]
            #~ 'maxCo'         + '\t' +    #outVar[2][1]
            #~ 'avgCoI'        + '\t' +    #outVar[2][2]
            #~ 'maxCoI'        + '\n'      #outVar[2][3]
          #~ ]
#~ 
#~ nLines = min([len(outVar[i][0]) for i in range(len(outVar))])            #get minimal list length
#~ 
#~ for i in range(nLines):
    #~ wrList.append(
        #~ "%5.5e\t"%outVar[0][1][i] +     #simulation time (s)
        #~ "%5.5e\t"%outVar[0][0][i] +     #adaptive time step (s)
        #~ "%5.5e\t"%outVar[1][0][i] +     #execution time (s)
        #~ "%5.5e\t"%outVar[1][1][i] +     #timeStep time (s)
        #~ "%10d\t"%outVar[1][2][i]   +    #simulation step (--)
        #~ "%5.5e\t"%outVar[2][0][i] +     #courant numbers
        #~ "%5.5e\t"%outVar[2][1][i] +
        #~ "%5.5e\t"%outVar[2][2][i] +
        #~ "%5.5e\n"%outVar[2][3][i]
    #~ )
    
#~ # -- save the results
#~ with open(
            #~ fileNm,
            #~ 'w'
        #~ ) as file:
    #~ file.writelines( wrList )
