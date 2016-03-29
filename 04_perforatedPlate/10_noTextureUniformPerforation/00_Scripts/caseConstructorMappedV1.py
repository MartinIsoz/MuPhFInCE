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
from fblockMeshGenV9 import fblockMeshGen                                 #blockMeshDict generation
#~ from finletBCWriter   import finletBCWriter                             #BC adjustment

#########EDITABLE#######################################################

#INPUT PARAMETERS=======================================================
# -- case defining parameters
Re      = 240                                                            #problem reynolds number
hIn     = 0.4e-3                                                        #liquid inlet height (m)
alpha   = math.pi/3                                                     #plate inclination angle
liqName = 'H2OCk' #DC05,DC10,H2O,SURF

# -- geometry and meshing parameters
aG      = 50.0e-3                                                       #geometry width
lG      = 60.0e-3                                                       #geometry length
hG      = 20.0e-3#7.0e-3                                                       #geometry height
dA      = 1.0*0.30e-3                                                       #width of 1 cell
dL      = 1.0*0.30e-3                                                       #length of 1 cell
dH      = 1.0*0.05e-3                                                       #height of 1 cell
diamH   = 3.00e-3                                                       #diameter of a hole
distHX  = 10.0e-3                                                       #distance between holes in x-direction
distHY  = 10.0e-3                                                       #distance between holes in y-direction
# Note: geometry cannot be really thin - it causes numerical instabilities
#       ("2D cells")

# -- case run properties
nCores      = 8                                                        #number of cores to run the case on
startTime   = 0.5                                                         #simulation startTime
endTime     = 0.6                                                        #simulation endTime
wrInt       = 0.001                                                      #simulation write interval
queName     = 'batch'                                                   #que name for altix
wallTime    = '300:00:00'                                               #walltime in hours for altix

#########PREFERABLY DO NOT EDIT#########################################

#COPY CASE BASICS FROM THE BASECASE=====================================
baseCase    = '../03_baseCaseMappedBC/'                             #folder with baseCase
caseDir     = ('../iF_Re' + 
                repr(round(Re,4)) + '_' + repr(round(alpha*180/math.pi)) + 
                '_' + liqName + '_PS_MP/'
                )

if os.path.isdir(caseDir):                                              #ensure, that the caseDir is clear
    sh.rmtree(caseDir)
    
sh.copytree(baseCase,caseDir)                                             #copy data to caseDir
#SPECIFY CURRENT SCRIPT VERSIONS========================================
blockMeshGen        = 'fblockMeshGenV9'
caseConstructor     = 'caseConstructorMappedV1'
postProc            = 'postProcMinimal'
postProcData        = 'postProcSaveData'
postProcGas         = 'postProcMinimal_gCC'
fluidData           = 'dfluidData'
#~ rivuletPostProc2Blender = 'rivuletPostProc2Blender'
#~ blenderPrep         = 'blenderPrepV2'


#COPY CURRENT SCRIPT VERSIONS===========================================
scFolder= '../00_Scripts/'                                              #folder with Scripts sources
scNames = [ blockMeshGen,                                               #preProcFunc - mesh gen.
            caseConstructor,                                            #copy current version of caseConstructor
            #~ 'finletBCWriter'                                            #preProcFunc - BC writer
            postProc,                                                   #case postprocessing (paraview)
            postProcGas,                                                #case postprocessing (paraview)
            postProcData,                                               #case postprocessing data export
            fluidData,                                                  #used database with fluid data
            #~ rivuletPostProc2Blender,                                    #export paraview->blender
            #~ blenderPrep,                                                #rivulet postprocessing (blender)
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
u0      = Re*mu/(rho*hIn)                                               #inlet velocity calculation
nu      = [mu/rho,muA/rhoA]
rho     = [rho,rhoA]
sigma   = [sigma]

#OPEN AUTOGENERATED README FILE=========================================
README  = open(caseDir + './README','a')                                #open file to append
# -- start by writing basic case info
README.write('\ncaseDir:' + caseDir + '\n\n')
README.write('Re        \t = \t ' + repr(round(Re,4)) + '\n')
README.write('hIn       \t = \t ' + repr(hIn*1e3) + ' mm\n')
README.write('alpha     \t = \t ' + repr(alpha/math.pi*180) + ' deg\n')
README.write('liqName   \t = \t ' + liqName + '\n')
README.write('nCores    \t = \t ' + repr(nCores) + '\n')
README.write('startTime \t = \t ' + repr(startTime) + ' s\n')
README.write('endTime   \t = \t ' + repr(endTime) + ' s\n')

#BLOCKMESHDICT FILE GENERATION==========================================
# -- prepara variables
geomSize= [aG,lG,hG]                                                    #variable with geometry dimensions
cellSize= [dA,dL,dH]                                                    #variable with cell dimensions
holePars= [diamH,distHX,distHY]                                         #variable with perforation parameters
# -- additional parameters
spGrad = 5                                                              #grading intensity in zDir of sparse block
mScale = 1                                                              #conversion to metres
#-----------------------------------------------------------------------
# FUNCTION CALL
#-----------------------------------------------------------------------
print 'WRITING BLOCKMESHDICT======================\n\n'
fblockMeshGen(caseDir,hIn,geomSize,cellSize,holePars,
    spGrad,mScale)
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

pVals   = ['value           uniform (' + repr(u0) + ' 0 0)']           #inlet liquid velocity speed

idStr   = ['value           uniform (0.01 0 0)']

# write everything to the file
with open(caseDir + './0.org/U', 'r') as file:
    # read a list of lines into data
    data = file.readlines()
    
for j in range(len(idStr)):
    for i in range(len(data)):
        fInd = data[i].find(idStr[j])
        if fInd>-1:
            data[i] = data[i][:fInd] + pVals[j] + ';\n'

with open(caseDir + './0.org/U', 'w') as file:
    file.writelines( data )
    README.writelines( data )                                           #write to readme

print 'u0 = (%5.5e 0 0) m/s'%u0
    
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
# createPatchDict
#-----------------------------------------------------------------------
#
# creates initial condition for the case (presence of the liquid)
#
README.write('\n createPatchDict\n')

idStr = ['offset']

pVals = ["(0 0 -%5.5e)"%hG]

# write everything to the file
with open(caseDir + './system/createPatchDict', 'r') as file:
    # read a list of lines into data
    data = file.readlines()
    
for j in range(len(idStr)):
    for i in range(len(data)):
        fInd = data[i].find(idStr[j])
        if fInd>-1:
            data[i] = data[i][:fInd] + idStr[j] + '\t\t\t' + pVals[j] + ';\n'

with open(caseDir + './system/createPatchDict', 'w') as file:
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
#~ #POST PROCESSING SCRIPT PREPARATION=====================================
#~ print 'PREPARING POSTPROCESSING SCRIPTS===========\n\n'
#~ README.write('\n POSTPROCESSING=====================================\n')
#~ #-----------------------------------------------------------------------
#~ # rivuletPostProc.py
#~ #-----------------------------------------------------------------------
#~ #
#~ # case description and so on
#~ #
#~ 
#~ README.write('\n' + rivuletPostProc + '.py\n')
#~ 
#~ idStr = ['nu0     =','gamma0  =','rho0    =','Q0      =',
         #~ 'alpha0  =',
         #~ ]
#~ wrStr = [("[%s]" % ', '.join(("%4.2e" % (e)) for e in nu)),
         #~ ("%4.2e" % (sigma[0])),
         #~ ("[%s]" % ', '.join(("%4.2e" % (e)) for e in rho)),
         #~ ("%4.2e" % (Q0)),
         #~ ("%4.0f" % (alpha/math.pi*180)),
         #~ ]
#~ 
#~ with open(caseDir + './' + rivuletPostProc + '.py', 'r') as file:
    #~ # read a list of lines into data
    #~ data = file.readlines()
    #~ 
#~ for j in range(len(idStr)):
    #~ for i in range(len(data)):
        #~ fInd = data[i].find(idStr[j])
        #~ if fInd>-1:
            #~ data[i] = data[i][:fInd] + idStr[j] + '\t' + wrStr[j] + '\n'
#~ 
#~ with open(caseDir + './' + rivuletPostProc + '.py', 'w') as file:
    #~ file.writelines( data )
    #~ README.writelines( data )
#~ #-----------------------------------------------------------------------
#~ # rivuletPostProc2Blender.py
#~ #-----------------------------------------------------------------------
#~ #
#~ # specifies to which version of blenderPrep write
#~ #
#~ 
#~ README.write('\n' + rivuletPostProc2Blender + '.py\n')
#~ 
#~ idStr = ['with open(',
         #~ ]
#~ wrStr = [blenderPrep + '.py',
         #~ ]
#~ endLStr=[", 'r') as file:\n"]
#~ 
#~ with open(caseDir + './' + rivuletPostProc2Blender + '.py', 'r') as file:
    #~ # read a list of lines into data
    #~ data = file.readlines()
    #~ 
#~ for j in range(len(idStr)):
    #~ for i in range(len(data)):
        #~ fInd = data[i].find(idStr[j])
        #~ if fInd>-1:
            #~ data[i] = data[i][:fInd] + idStr[j] + '\t' + "'%s'"%wrStr[j] + '%s'%endLStr[j]
#~ 
#~ with open(caseDir + './' + rivuletPostProc2Blender + '.py', 'w') as file:
    #~ file.writelines( data )
    #~ README.writelines( data )
#~ 
#~ print 'DONE=======================================\n\n'
#~ #-----------------------------------------------------------------------
#~ # blenderPrep.py
#~ #-----------------------------------------------------------------------
#~ #
#~ # modifies script for the postprocessing in blender
#~ #
#~ README.write('\n' + blenderPrep + '.py\n')
#~ 
#~ idStr = ['plateIncl   =',
         #~ 'mDot        =',                                               #!!kg/s->g/s
         #~ 'liqName     =',
         #~ 'strTime     =',
         #~ 'endTime     =',
         #~ 'tStep       =',
         #~ ]
#~ wrStr = [(" %5.5e" % (alpha)),
         #~ (" %5.5e" % (1e3*mDot)),
         #~ (" %5s" % ('"' + liqName + '"')),
         #~ (" %5.2f" % (startTime)),
         #~ (" %5.2f" % (endTime)),
         #~ (" %5.4f" % (wrInt)),
         #~ ]
#~ 
#~ with open(caseDir + './' + blenderPrep + '.py', 'r') as file:
    #~ # read a list of lines into data
    #~ data = file.readlines()
    #~ 
#~ for j in range(len(idStr)):
    #~ for i in range(len(data)):
        #~ fInd = data[i].find(idStr[j])
        #~ if fInd>-1:
            #~ data[i] = data[i][:fInd] + idStr[j] + wrStr[j] + '\n'
#~ 
#~ with open(caseDir + './' + blenderPrep + '.py', 'w') as file:
    #~ file.writelines( data )
    #~ README.writelines( data )
#~ 
#~ print 'DONE=======================================\n\n'
#CLOSE THE AUTOGENERATED README FILE====================================
README.write('// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * // \n\n')
README.close()
