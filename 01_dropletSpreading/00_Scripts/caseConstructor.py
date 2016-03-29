#!/usr/bin/python

#FILE DESCRIPTION=======================================================
#~ Python script used for foam case construction (as automatic, as
#~ possible)
#~
#~ NOTES:
    #~ - mesh grading in z direction
    
#~ USAGE:
    #~ - modify and run the script

#~ TO DO:
   


#LICENSE================================================================
#  caseConstructor.py
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
#~ from finletBCWriter   import finletBCWriter                             #BC adjustment

#########EDITABLE#######################################################

#INPUT PARAMETERS=======================================================
# -- case defining parameters
r0      = 2.0e-3                                                        #initial drop radius
h0      = 0.7e-3                                                        #initial drop height
alpha   = 0#math.pi/3                                                     #plate inclination angle
liqName = "DC10" #DC05,DC10,H2O,H2OCk,SURF

# -- geometry and meshing parameters
lG      = 10.0e-3                                                       #geometry length
aG      =  0.1e-3                                                       #geometry width
#~ aG      =  lG                                                        #geometry width
hG      =  2.0e-3                                                       #geometry height
dL      = 0.08*1.0e-4                                                    #length of 1 cell
dA      =  aG                                                           #width of 1 cell
#~ dA      =  dL                                                        #width of 1 cell
dH      = 0.08*1.0e-4                                                    #height of 1 cell
# Note: geometry cannot be really thin - it causes numerical instabilities
#       ("2D cells")

# -- PIMPLE algorithm settings
nOuterCorrectors    = 50                                                #maximal number of PIMPLE iterations
nCorrectors         = 1                                                 #number of correctors in PISO loop
nNonOrthoCorrectors = 5                                                 #number of non-orthogonal correctors in each PIMPLE iteration

# -- case run properties
nCores      = 4                                                        #number of cores to run the case on
startTime   = 0                                                         #simulation startTime
endTime     = 0.3                                                       #simulation endTime
wrInt       = 0.01                                                      #simulation write interval
queName     = 'batch'                                                   #que name for altix
wallTime    = '300:00:00'                                               #walltime in hours for altix

#########PREFERABLY DO NOT EDIT#########################################

#COPY CASE BASICS FROM THE BASECASE=====================================
baseCase    = '../01_baseCase/'                                         #folder with baseCase
if aG/dA > 1:                                                           #see if the case is 2D or 3D
    nDims = 3
else:
    nDims = 2
    
caseDir     = ('../iF_Drop' + repr(nDims) + 'D' + 
                '_h0%.1e'%h0     + 
                '_r0%.1e'%r0     +
                '_%2.1f'%alpha   + 
                '_' + liqName + '_L3/'
                )

if os.path.isdir(caseDir):                                              #ensure, that the caseDir is clear
    sh.rmtree(caseDir)
    
sh.copytree(baseCase,caseDir)                                             #copy data to caseDir
#SPECIFY CURRENT SCRIPT VERSIONS========================================
blockMeshGen        = 'fblockMeshGen'
caseConstructor     = 'caseConstructor'
#~ postProc            = 'postProcMinimal'
#~ postProcData        = 'postProcSaveData'
fluidData           = 'dfluidData'
simControl          = 'procLogLocal'


#COPY CURRENT SCRIPT VERSIONS===========================================
scFolder= '../00_Scripts/'                                              #folder with Scripts sources
scNames = [ blockMeshGen,                                               #preProcFunc - mesh gen.
            caseConstructor,                                            #copy current version of caseConstructor
            #~ 'finletBCWriter'                                            #preProcFunc - BC writer
            #~ postProc,                                                   #case postprocessing (paraview)
            #~ postProcData,                                               #case postprocessing data export
            fluidData,                                                  #used database with fluid data
            #~ rivuletPostProc2Blender,                                    #export paraview->blender
            #~ blenderPrep,                                                #rivulet postprocessing (blender)
            simControl                                                  #script for case run control
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
nu      = [mu/rho,muA/rhoA]
rho     = [rho,rhoA]
sigma   = [sigma]

#OPEN AUTOGENERATED README FILE=========================================
README  = open(caseDir + './README','a')                                #open file to append
# -- start by writing basic case info
README.write('\ncaseDir:' + caseDir + '\n\n')
README.write('h0        \t = \t ' + repr(h0*1e3) + ' mm\n')
README.write('r0        \t = \t ' + repr(r0*1e3) + ' mm\n')
README.write('alpha     \t = \t ' + repr(alpha/math.pi*180) + ' deg\n')
README.write('liqName   \t = \t ' + liqName + '\n')
README.write('nCores    \t = \t ' + repr(nCores) + '\n')
README.write('startTime \t = \t ' + repr(startTime) + ' s\n')
README.write('endTime   \t = \t ' + repr(endTime) + ' s\n')

#BLOCKMESHDICT FILE GENERATION==========================================
# -- prepara variables
geomSize= [aG,lG,hG]                                                    #variable with geometry dimensions
cellSize= [dA,dL,dH]                                                    #variable with cell dimensions
# -- additional parameters
spGrad = 5                                                              #grading intensity in zDir of sparse block
mScale = 1                                                              #conversion to metres
#-----------------------------------------------------------------------
# FUNCTION CALL
#-----------------------------------------------------------------------
print 'WRITING BLOCKMESHDICT======================\n\n'
fblockMeshGen(caseDir,h0,geomSize,cellSize,
    spGrad,mScale)
print 'DONE=======================================\n\n'


#BC FILES MODIFICATION==================================================
#-----------------------------------------------------------------------
# FUNCTION CALL
#-----------------------------------------------------------------------
print 'ADJUSTING BC===============================\n\n'
README.write('\n 0.org==============================================\n')    
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
#~ alpha = 0*math.pi/3                                                      #plate inclination
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
# not really necessary for this problem - I have prepared the filled
# inlet as a start
#
README.write('\n setFieldsDict\n')

# necassary values calculation
R = h0/2 + r0**2/(2*h0)                                                 #cylinder diameter
d = R-h0                                                                #how much below the plate is the circle center

if nDims == 2:
    pVals   = [
                '(%5.5f 0 %5.5f)'%(lG/2,-d),
                '(%5.5f %5.5f %5.5f)'%(lG/2,aG,-d),
                '%5.5f'%R,
              ]
    idStr   = ['p1 ','p2 ','radius ' ]
    setFieldsDict = 'setFieldsDict2D'
else:
    pVals   = [
                '(%5.5f %5.5f %5.5f)'%(lG/2,aG/2,-d),
                '%5.5f'%R,
              ]
    idStr   = ['centre ','radius ' ]
    setFieldsDict = 'setFieldsDict3D'

# write everything to the file
with open(caseDir + './system/' + setFieldsDict, 'r') as file:
    # read a list of lines into data
    data = file.readlines()
    
for j in range(len(idStr)):
    for i in range(len(data)):
        fInd = data[i].find(idStr[j])
        if fInd>-1:
            data[i] = data[i][:fInd] + idStr[j]  + pVals[j] + ';\n'

with open(caseDir + './system/setFieldsDict', 'w') as file:
    file.writelines( data )
    README.writelines( data )                                           #write to readme
print 'DONE=======================================\n\n'
    
#-----------------------------------------------------------------------
# decomposeParDict
#-----------------------------------------------------------------------
#
# creates initial condition for the case (presence of the liquid)
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
#~ 
print 'DONE=======================================\n\n'
#CLOSE THE AUTOGENERATED README FILE====================================
README.write('// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * // \n\n')
README.close()
