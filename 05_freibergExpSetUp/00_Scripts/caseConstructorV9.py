#!/usr/bin/python

#FILE DESCRIPTION=======================================================
#~ Python script used for foam case construction (as automatic, as
#~ possible)
#~
#~ NOTES:
    
    
#~ USAGE:
    #~ - modify and run the script

#~ TO DO:
   


#LICENSE================================================================
#  caseConstructor.py
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

#########DO NOT EDIT####################################################

#IMPORT BLOCK===========================================================
import os
import math
import io
import sys
import shutil as sh
#~ import numpy as np
#~ import matplotlib.pyplot as plt
# special functions
#~ from scipy.optimize import fsolve                                       #NAE solver
#IMPORT BLOCK-CUSTOM====================================================
# custom functions------------------------------------------------------
from dfluidData import dfluidData
from fblockMeshGen import fblockMeshGen                                 #blockMeshDict generation
#~ from finletBCWriter   import finletBCWriter                          #BC adjustment
from fprepIC_noGravityV4 import fprepIC_noGravity                         #initial condition (setFields)

#LOCAL FUNCTIONS DEFINITIONS============================================
def meshSizePars(Q0,liqName):
    #function/dictionary for easy switching between the necessary mesh
    #sizes
    #ugly coding BUT for each pair liquid-flow rate returns
    #corresponding mesh size as a vector [aD,aT,hC]
    #
    # aD    ... width of the dense block
    # aT    ... total mesh width
    # hC    ... total mesh height
    Q0 = Q0*1e6                                                         #easier comparison
    if liqName=="DC10" or liqName=="DC05":
        if Q0 <= 0.5:
            return [20e-3,40e-3,3e-3]
        elif Q0 > 0.5 and Q0 <= 2.0:
            return [30e-3,55e-3,5e-3]
        else:
            return [40e-3,75e-3,5e-3]
    else:
        if Q0 <= 3.5:
            return [20e-3,40e-3,3e-3]
        elif Q0 > 3.5 and Q0 <= 5.8:
            return [20e-3,40e-3,6e-3]
        else:
            return [20e-3,40e-3,10e-3]

#########EDITABLE#######################################################

#INPUT PARAMETERS=======================================================
# -- case defining parameters
Q0      = 0.26*1e-6                                                   #initial vol. flow rate (mL->m3/s)
alpha   = 60*math.pi/180                                                     #plate inclination angle
liqName = 'DC05' #DC05,DC10,H2O,SURF
a0Theor = 4.0*1e-3                                                      #initial rivulet width for theoretical model

# -- mesh size (changeable properties)
# geometry dimensions
[aD,aT,hC] = meshSizePars(Q0,liqName)

# -- PIMPLE algorithm settings
nOuterCorrectors    = 50                                                #maximal number of PIMPLE iterations
nCorrectors         = 1                                                 #number of correctors in PISO loop
nNonOrthoCorrectors = 4                                                 #number of non-orthogonal correctors in each PIMPLE iteration

# Note: nNonOrthCorrectors should be 3-5 for coarse mesh run
# Note: nNonOrthCorrectors should be 4-6 for fine   mesh run

# -- case run properties
nCores      = 4                                                        #number of cores to run the case on
startTime   = 0                                                         #simulation startTime
endTime     = 0.1                                                        #simulation endTime
wrInt       = 0.004                                                      #simulation write interval
queName     = 'batch'                                                   #que name for altix
wallTime    = '300:00:00'                                               #walltime in hours for altix

CHILD       = False                                                     #is the current case CHILD
# -- NOTE: CHILD means, that there is another case from which the
#          initial fields should be mapped
#          CONSEQUENCES:    - PBS should start CHILD after the PARENT
#                             case finished
#                           - include MAPFIELDS in ALLRUN script
#                           - PARENT case has to be specified

if CHILD:
    # -- PARENT case specification
    Q0PARENT      = 4.8133*1e-6                                         #parent case flow rate (mL->m3/s)
    alphaPARENT   = math.pi/3                                           #PARENT plate inclination angle
    liqNamePARENT = liqName                                             #ONLY FOR THE SAME LIQUID
    PARENT        = (
                        'iF_'
                        +
                        repr(round(Q0PARENT*1e6,4))                     #PARENT case name specification
                        +
                        '_'
                        +
                        repr(round(alphaPARENT*180/math.pi))
                        +
                        '_'
                        +
                        liqNamePARENT
                    )
    endTimePARENT = 10                                                  #which folder to map
    

#########PREFERABLY DO NOT EDIT#########################################

#COPY CASE BASICS FROM THE BASECASE=====================================
baseCase    = '../01_baseCase/'                                         #folder with baseCase
caseDir     = ('../iF_' + 
                repr(round(Q0*1e6,4)) + '_' + repr(round(alpha*180/math.pi)) + 
                '_' + liqName + 'V2/'
                )

if os.path.isdir(caseDir):                                              #ensure, that the caseDir is clear
    sh.rmtree(caseDir)
    
sh.copytree(baseCase,caseDir)                                             #copy data to caseDir
#SPECIFY CURRENT SCRIPT VERSIONS========================================
blockMeshGen        = 'fblockMeshGen'
caseConstructor     = 'caseConstructorV9'
genPostProc         = 'postProcMinimalV2'
rivuletPostProc     = 'rivuletPostProc'
rivuletPostProcSaveData = 'rivuletPostProcSaveData'
rivuletPostProc2Blender = 'rivuletPostProc2Blender'
blenderPrep         = 'blenderPrepV2'
simControl          = 'procLogLocal'


#COPY CURRENT SCRIPT VERSIONS===========================================
scFolder= '../00_Scripts/'                                              #folder with Scripts sources
scNames = [ blockMeshGen,                                               #preProcFunc - mesh gen.
            caseConstructor,                                            #copy current version of caseConstructor
            #~ 'finletBCWriter'                                            #preProcFunc - BC writer
            genPostProc,                                                #general postprocessing
            rivuletPostProc,                                            #rivulet postprocessing (paraview)
            rivuletPostProcSaveData,                                    #data export from postproc (paraview)
            rivuletPostProc2Blender,                                    #export paraview->blender
            blenderPrep,                                                #rivulet postprocessing (blender)
            simControl                                                  #script to see the simulation progress
            ]                                   
for scName in scNames:
    sh.copyfile(scFolder + scName + '.py',caseDir + scName + '.py')     #copy current script version

#CASE CONSTANTS AND CALCULATIONS========================================
# input data------------------------------------------------------------
# -- global parameters
g       = 9.81                                                          #grav. acc., m/s2

# -- liquid properties
[sigma,rho,mu,theta0,thetaA,thetaR] = dfluidData(liqName)
[_,rhoA,muA,_,_,_]                  = dfluidData('AIR')
#~ NOTE: liquid properties are stored in a special dictionary
#~ sigma       ... surface tension coefficient of the liquid, N/m
#~ rho         ... density of the liquid, kg/m3
#~ mu          ... liquid dynamic viscosity, Pas
#~ theta0,thetaA,thetaR ... equilibrium, advancing and receding contact
#~                          angles

# further calculations
mDot    = Q0*rho                                                        #mass flow rate calculation
nu      = [mu/rho,muA/rhoA]
rho     = [rho,rhoA]
sigma   = [sigma]

#OPEN AUTOGENERATED README FILE=========================================
README  = open(caseDir + './README','a')                                #open file to append
# -- start by writing basic case info
README.write('\ncaseDir:' + caseDir + '\n\n')
README.write('Q0        \t = \t ' + repr(round(Q0*1e6,4)) + ' mL/s\n')
README.write('alpha     \t = \t ' + repr(alpha/math.pi*180) + ' deg\n')
README.write('liqName   \t = \t ' + liqName + '\n')
README.write('nCores    \t = \t ' + repr(nCores) + '\n')
README.write('startTime \t = \t ' + repr(startTime) + ' s\n')
README.write('endTime   \t = \t ' + repr(endTime) + ' s\n')

#BLOCKMESHDICT FILE GENERATION==========================================

#-----------------------------------------------------------------------
# GEOMETRY DATA
#-----------------------------------------------------------------------

# central point
x0, y0, z0 				= 0.0, 0.0, 0.0
#~ # geometry dimensions
cL, cW, cH, iH, tL		= 300.0e-3, aT, hC, 10.0e-3, 10.0e-3
# width of the dense block (to contain the rivulet)
dbW 					= aD
# in which part (from the center point) should be the inlet divided
nDiv 					= 3

# length scale - cell height
d0 						= 1

#-----------------------------------------------------------------------
# MESH DATA
#-----------------------------------------------------------------------
# number of cells in each direction for each part of the mesh
nCellsXDL = int(cL*1e3)	#number of cells in dense long blocks - xDirection
nCellsXDS = 20	#number of cells in dense short blocks - xDirection
nCellsYD  = int(dbW*1e3)#number of cells in dense long & short blocks - yDirection
nCellsZD  = int(5*cH*1e3) 	#number of cells in dense long & short blocks - zDirection

nCellsXSL = int(round(nCellsXDL/5))#number of cells in sparse long blocks - xDirection
nCellsXSS = int(round(nCellsXDS/5))#number of cells in sparse short blocks - xDirection
nCellsYS  = int(round(nCellsYD/5))#number of cells in sparse long & short blocks - yDirection
nCellsZS  = int(round(nCellsZD/3))#number of cells in sparse long & short blocks - zDirection

nCellsZI  = 40  #number of cells in inlet z direction

#
#-----------------------------------------------------------------------
# mesh grading - not implemented
#~ grDX, grDY, grDZ = 1.0, 1.0, 1.0                                        #grading in dense block
#~ grSX, grSY, grSZ = 1.0, 1.0, 1.0                                        #gradins in sparse block

# scale (to meters)
mScale = 1
#-----------------------------------------------------------------------
# FUNCTION CALL
#-----------------------------------------------------------------------
print 'WRITING BLOCKMESHDICT======================\n\n'
fblockMeshGen(caseDir,x0,y0,z0,cL,cW,cH,iH,tL,dbW,nDiv,d0,
    nCellsXDL,nCellsXDS,nCellsYD,nCellsZD,
    nCellsXSL,nCellsXSS,nCellsYS,nCellsZS,nCellsZI,
    mScale)
print 'DONE=======================================\n\n'


#BC FILES MODIFICATION==================================================
#-----------------------------------------------------------------------
# FUNCTION CALL
#-----------------------------------------------------------------------
print 'ADJUSTING BC===============================\n\n'
README.write('\n 0.org==============================================\n')
#~ finletBCWriter(a0,h0,eps,aaRat,beta,rho,g,mu,sigma,nCellsW,nCellsL)
#-----------------------------------------------------------------------
# U
#-----------------------------------------------------------------------
#
# Boundary conditions for the velocity field
#
README.write('\n U\n')

pVals   = [repr(mDot)]                                                   #mass flow rate in rivulet

idStr   = ['massFlowRate    constant ']

# write everything to the file
with open(caseDir + './0.org/U', 'r') as file:
    # read a list of lines into data
    data = file.readlines()
    
for j in range(len(idStr)):
    for i in range(len(data)):
        fInd = data[i].find(idStr[j])
        if fInd>-1:
            data[i] = data[i][:fInd] + idStr[j] + '\t' + pVals[j] + ';\n'

with open(caseDir + './0.org/U', 'w') as file:
    file.writelines( data )
    README.writelines( data )                                           #write to readme
    
#-----------------------------------------------------------------------
# alpha.liquid
#-----------------------------------------------------------------------
#
# Boundary conditions for the velocity field
#
README.write('\n alpha.liquid\n')

pVals   = [repr(theta0),repr(thetaA),repr(thetaR)]                      #contact angles

idStr   = ['theta0','thetaA','thetaR']

# write everything to the file
with open(caseDir + './0.org/alpha.liquid', 'r') as file:
    # read a list of lines into data
    data = file.readlines()
    
for j in range(len(idStr)):
    for i in range(len(data)):
        fInd = data[i].find(idStr[j])
        if fInd>-1:
            data[i] = data[i][:fInd] + idStr[j] + '\t\t\t' + pVals[j] + ';\n'

with open(caseDir + './0.org/alpha.liquid', 'w') as file:
    file.writelines( data )
    README.writelines( data )                                           #write to readme
print 'DONE=======================================\n\n'

#CONSTANTS DIRECTORY FILES MODIFICATIONS================================
print 'ADJUSTING FILES IN ./CONSTANTS=============\n\n'
README.write('\n CONSTANTS==========================================\n')
#-----------------------------------------------------------------------
# g
#-----------------------------------------------------------------------
#
# defines gravitational acceleration (prepared for inclined plate)
#
README.write('\n g\n')

# general properties
gx    = math.sin(alpha)*g
gy    = 0.0
gz    = -math.cos(alpha)*g

idStr = 'value'

# write everything to the file
with open(caseDir + './constant/g', 'r') as file:
    # read a list of lines into data
    data = file.readlines()
    
for i in range(len(data)):
    fInd = data[i].find(idStr)
    if fInd>-1:
        data[i] = (data[i][:fInd] + idStr + '\t\t\t(' 
        + repr(gx) + '\t' + repr(gy) + '\t' + repr(gz) + ');\n')

with open(caseDir + './constant/g', 'w') as file:
    file.writelines( data )
    README.writelines( data )                                           #write to readme
    
#-----------------------------------------------------------------------
# transportProperties
#-----------------------------------------------------------------------
#
# defines liquid properties (to be red by oF)
#
README.write('\n transportProperties\n')

idStr = ['nu [ 0 2 -1 0 0 0 0 ]',
         'rho [ 1 -3 0 0 0 0 0 ]',
         'sigma [ 1 0 -2 0 0 0 0 ]']         

pVals = [nu,rho,sigma]

# write everything to the file
with open(caseDir + './constant/transportProperties', 'r') as file:
    # read a list of lines into data
    data = file.readlines()
    
for j in range(len(idStr)):
    k = 0
    for i in range(len(data)):
        fInd = data[i].find(idStr[j])
        if fInd>-1:
            data[i] = data[i][:fInd] + idStr[j] + '\t' + repr(pVals[j][k]) + ';\n'
            k = k+1

with open(caseDir + './constant/transportProperties', 'w') as file:
    file.writelines( data )
    README.writelines( data )                                           #write to readme
    
print 'DONE=======================================\n\n'   
#SYSTEM DIRECTORY FILES MODIFICATIONS===================================
print 'ADJUSTING FILES IN ./SYSTEM================\n\n'
README.write('\n SYSTEM=============================================\n')
#-----------------------------------------------------------------------
# setFieldsDict
#-----------------------------------------------------------------------
#
# the modification is executed by an external function
#
README.write('\n setFieldsDict - external function\n')

pltFlag = True                                                          #do I want the control plot?
a0      = a0Theor                                                       #initial rivulet width
l       = 3.0e-5                                                        #interim region length scale


fprepIC_noGravity(caseDir,a0,Q0,liqName,l,alpha,cL,nCellsXDL,cH,nCellsZD,pltFlag)

    
#-----------------------------------------------------------------------
# decomposeParDict
#-----------------------------------------------------------------------
#
# decomposes the case for run on multiple cores
#
README.write('\n decomposeParDict\n')

idStr = ['numberOfSubdomains ']

pVals = [repr(nCores)]

# write everything to the file
with open(caseDir + './system/decomposeParDict', 'r') as file:
    # read a list of lines into data
    data = file.readlines()
    
for j in range(len(idStr)):
    for i in range(len(data)):
        fInd = data[i].find(idStr[j])
        if fInd>-1:
            data[i] = data[i][:fInd] + idStr[j] + '\t' + pVals[j] + ';\n'

with open(caseDir + './system/decomposeParDict', 'w') as file:
    file.writelines( data )
    README.writelines( data )                                           #write to readme
#-----------------------------------------------------------------------
# controlDict
#-----------------------------------------------------------------------
#
# creates initial condition for the case (presence of the liquid)
#
README.write('\n controlDict\n')

idStr = ['startTime ','endTime ','writeInterval ']

pVals = [repr(startTime),repr(endTime),repr(wrInt)]

# write everything to the file
with open(caseDir + './system/controlDict', 'r') as file:
    # read a list of lines into data
    data = file.readlines()
    
for j in range(len(idStr)):
    for i in range(len(data)):
        fInd = data[i].find(idStr[j])
        if fInd>-1:
            data[i] = data[i][:fInd] + idStr[j] + '\t' + pVals[j] + ';\n'

with open(caseDir + './system/controlDict', 'w') as file:
    file.writelines( data )
    README.writelines( data )                                           #write to readme
    
#-----------------------------------------------------------------------
# fvSolution
#-----------------------------------------------------------------------
#
# set up parameters for the case running
#
README.write('\n fvSolution\n')

# read the file
with open(caseDir + './system/fvSolution', 'r') as file:
    # read a list of lines into data
    data = file.readlines()

# update information on number of cells in coarses level for multigrid
idStr = ['nCellsInCoarsestLevel ']

pVals = [repr(10*nCores)]
    
for j in range(len(idStr)):
    for i in range(len(data)):
        fInd = data[i].find(idStr[j])
        if fInd>-1:
            data[i] = data[i][:fInd] + idStr[j] + pVals[j] + ';\n'
            
idStr = [
            'nOuterCorrectors    ',
            'nCorrectors         ',
            'nNonOrthogonalCorrectors ',
        ]
        
pFlag = False

pVals = [
            repr(nOuterCorrectors),
            repr(nCorrectors),
            repr(nNonOrthoCorrectors),
        ]
    
for j in range(len(idStr)):
    for i in range(len(data)):
        if data[i].find('PIMPLE') >-1:                                  #modify only the PIMPLE algorithm
            pFlag = True
        if pFlag:
            fInd = data[i].find(idStr[j])
            if fInd>-1:
                data[i] = data[i][:fInd] + idStr[j] + pVals[j] + ';\n'
            if data[i].find('}') == 0:
                pFlag = False                                           #stop when you reach the end of its settings
    pFlag = False                                                       #stop at the end of file
            
# update the PIMPLE algorithm settings

with open(caseDir + './system/fvSolution', 'w') as file:
    file.writelines( data )
    README.writelines( data )                                           #write to readme

print 'DONE=======================================\n\n'   
#RUN SCRIPTS PREPARATION================================================
print 'PREPARING RUN SCRIPTS======================\n\n'
README.write('\n RUN SCRIPTS========================================\n')
#-----------------------------------------------------------------------
# ./Allrun-parallel
#-----------------------------------------------------------------------
#
README.write('\n Allrun-parallel\n')

idStr = ['runParallel $application ']

pVals = [repr(nCores)]

# write everything to the file
with open(caseDir + './Allrun-parallel', 'r') as file:
    # read a list of lines into data
    data = file.readlines()
    
for j in range(len(idStr)):
    for i in range(len(data)):
        fInd = data[i].find(idStr[j])
        if fInd>-1:
            data[i] = data[i][:fInd] + idStr[j] + ' ' + pVals[j] + '\n'

with open(caseDir + './Allrun-parallel', 'w') as file:
    file.writelines( data )
    README.writelines( data )                                           #write to readme
    
#-----------------------------------------------------------------------
# ./Allrun.pre (ONLY IF THE CASE IS A CHILD)
#-----------------------------------------------------------------------
#
if CHILD:
    README.write('\n Allrun.pre - CHILD CASE\n')
    
    idStr = [
                '#PARENT=',
                '#mapFields ../$PARENT -sourceTime latestTime -consistent'
            ]
    
    pVals = [
                'PARENT=' + PARENT,
                'mapFields ../$PARENT -sourceTime latestTime -consistent'
            ]
    
    # write everything to the file
    with open(caseDir + './Allrun.pre', 'r') as file:
        # read a list of lines into data
        data = file.readlines()
        
    for j in range(len(idStr)):
        for i in range(len(data)):
            fInd = data[i].find(idStr[j])
            if fInd>-1:
                data[i] = pVals[j] + '\n'                               #in this case, I am replacing the whole row
    
    with open(caseDir + './Allrun.pre', 'w') as file:
        file.writelines( data )
        README.writelines( data )                                           #write to readme
    
#-----------------------------------------------------------------------
# ./of.sh
#-----------------------------------------------------------------------
#
README.write('\n of.sh\n')

idStr = [
            '#PBS -N ',
            '#PBS -q ',
            '#PBS -l nodes=1:ppn=',
            '#PBS -l walltime=',
            'caseDir=',
            ]

caseName = caseDir.split('/')[-2]

pVals = [caseName+'.pbs',queName,repr(nCores),wallTime,"'" + caseName + "'"]

# write everything to the file
with open(caseDir + './of.sh', 'r') as file:
    # read a list of lines into data
    data = file.readlines()
    
for j in range(len(idStr)):
    for i in range(len(data)):
        fInd = data[i].find(idStr[j])
        if fInd>-1:
            data[i] = data[i][:fInd] + idStr[j] + pVals[j] + '\n'

with open(caseDir + './of.sh', 'w') as file:
    file.writelines( data )
    README.writelines( data )                                           #write to readme
    
print 'DONE=======================================\n\n'
#POST PROCESSING SCRIPT PREPARATION=====================================
print 'PREPARING POSTPROCESSING SCRIPTS===========\n\n'
README.write('\n POSTPROCESSING=====================================\n')
#-----------------------------------------------------------------------
# rivuletPostProc.py
#-----------------------------------------------------------------------
#
# case description and so on
#

README.write('\n' + rivuletPostProc + '.py\n')

idStr = ['nu0     =','gamma0  =','rho0    =','Q0      =',
         #~ 'a0      =','h0      =','eps     =',
         'alpha0  =',
         ]
wrStr = [("[%s]" % ', '.join(("%4.2e" % (e)) for e in nu)),
         ("%4.2e" % (sigma[0])),
         ("[%s]" % ', '.join(("%4.2e" % (e)) for e in rho)),
         ("%4.2e" % (Q0)),
         #~ ("%4.2e" % (a0)),
         #~ ("%4.2e" % (h0)),
         #~ ("%4.2e" % (eps)),
         ("%4.0f" % (alpha/math.pi*180)),
         ]

with open(caseDir + './' + rivuletPostProc + '.py', 'r') as file:
    # read a list of lines into data
    data = file.readlines()
    
for j in range(len(idStr)):
    for i in range(len(data)):
        fInd = data[i].find(idStr[j])
        if fInd>-1:
            data[i] = data[i][:fInd] + idStr[j] + '\t' + wrStr[j] + '\n'

with open(caseDir + './' + rivuletPostProc + '.py', 'w') as file:
    file.writelines( data )
    README.writelines( data )
#-----------------------------------------------------------------------
# rivuletPostProcSaveData.py
#-----------------------------------------------------------------------
#
# case description and so on
#

README.write('\n' + rivuletPostProcSaveData + '.py\n')

idStr = ['nu0     =','gamma0  =','rho0    =','Q0      =',
         #~ 'a0      =','h0      =','eps     =',
         'alpha0  =',
         ]
wrStr = [("[%s]" % ', '.join(("%4.2e" % (e)) for e in nu)),
         ("%4.2e" % (sigma[0])),
         ("[%s]" % ', '.join(("%4.2e" % (e)) for e in rho)),
         ("%4.2e" % (Q0)),
         #~ ("%4.2e" % (a0)),
         #~ ("%4.2e" % (h0)),
         #~ ("%4.2e" % (eps)),
         ("%4.0f" % (alpha/math.pi*180)),
         ]

with open(caseDir + './' + rivuletPostProcSaveData + '.py', 'r') as file:
    # read a list of lines into data
    data = file.readlines()
    
for j in range(len(idStr)):
    for i in range(len(data)):
        fInd = data[i].find(idStr[j])
        if fInd>-1:
            data[i] = data[i][:fInd] + idStr[j] + '\t' + wrStr[j] + '\n'

with open(caseDir + './' + rivuletPostProc + '.py', 'w') as file:
    file.writelines( data )
    README.writelines( data )
#-----------------------------------------------------------------------
# rivuletPostProc2Blender.py
#-----------------------------------------------------------------------
#
# specifies to which version of blenderPrep write
#

README.write('\n' + rivuletPostProc2Blender + '.py\n')

idStr = ['with open(',
         ]
wrStr = [blenderPrep + '.py',
         ]
endLStr=[", 'r') as file:\n"]

with open(caseDir + './' + rivuletPostProc2Blender + '.py', 'r') as file:
    # read a list of lines into data
    data = file.readlines()
    
for j in range(len(idStr)):
    for i in range(len(data)):
        fInd = data[i].find(idStr[j])
        if fInd>-1:
            data[i] = data[i][:fInd] + idStr[j] + '\t' + "'%s'"%wrStr[j] + '%s'%endLStr[j]

with open(caseDir + './' + rivuletPostProc2Blender + '.py', 'w') as file:
    file.writelines( data )
    README.writelines( data )

print 'DONE=======================================\n\n'
#-----------------------------------------------------------------------
# blenderPrep.py
#-----------------------------------------------------------------------
#
# modifies script for the postprocessing in blender
#
README.write('\n' + blenderPrep + '.py\n')

idStr = ['plateIncl   =',
         'mDot        =',                                               #!!kg/s->g/s
         'liqName     =',
         'strTime     =',
         'endTime     =',
         'tStep       =',
         ]
wrStr = [(" %5.5e" % (alpha)),
         (" %5.5e" % (1e3*mDot)),
         (" %5s" % ('"' + liqName + '"')),
         (" %5.2f" % (startTime)),
         (" %5.2f" % (endTime)),
         (" %5.4f" % (wrInt)),
         ]

with open(caseDir + './' + blenderPrep + '.py', 'r') as file:
    # read a list of lines into data
    data = file.readlines()
    
for j in range(len(idStr)):
    for i in range(len(data)):
        fInd = data[i].find(idStr[j])
        if fInd>-1:
            data[i] = data[i][:fInd] + idStr[j] + wrStr[j] + '\n'

with open(caseDir + './' + blenderPrep + '.py', 'w') as file:
    file.writelines( data )
    README.writelines( data )

print 'DONE=======================================\n\n'
#CLOSE THE AUTOGENERATED README FILE====================================
README.write('// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * // \n\n')
README.close()
