#!/usr/bin/python

#FILE DESCRIPTION=======================================================
#~ Python script used for foam case construction (as automatic, as
#~ possible)
#~
#~ NOTES:
    #~ - before running, the main file has to be highlighted
    
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

#IMPORT BLOCK===========================================================
import os
import math
import io
import sys
import shutil as sh
import numpy as np
import matplotlib.pyplot as plt
# special functions
from scipy.optimize import fsolve                                       #NAE solver

#IMPORT BLOCK-CUSTOM====================================================
# custom functions------------------------------------------------------
from dfluidData import dfluidData
from fblockMeshGen_rPFF import fblockMeshGen                            #blockMeshDict generation
from finletBCWriter_rPFF   import finletBCWriter                        #BC adjustment

#########EDITABLE#######################################################

#INPUT PARAMETERS=======================================================
# -- case defining parameters
Q0      = 20*1e-6                                                   #initial vol. flow rate (mL->m3/s)
alpha   = math.pi/3                                                     #plate inclination angle
liqName = 'DC05' #DC05,DC10,H2O,SURF

# -- case run properties
nCores      = 8                                                        #number of cores to run the case on
startTime   = 0.0                                                       #simulation startTime
endTime     = 20.0                                                        #simulation endTime
wrInt       = 0.04                                                      #simulation write interval

#########PREFERABLY DO NOT EDIT#########################################

#COPY CASE BASICS FROM THE BASECASE=====================================
baseCase    = '/media/martin/Data_3/05_PlateDCases/01_baseCase_rPFF/'        #folder with baseCase
#~ baseCase    = '/home/martin/Documents/Phd/05_PlateDCases/01_baseCase_rPFF/'        #folder with baseCase
caseDir     = ('/media/martin/Data_3/05_PlateDCases/rPFF_' + 
#~ caseDir     = ('/home/martin/Documents/Phd/05_PlateDCases/rPFF_' + 
                repr(round(Q0*1e6,4)) + '_' + repr(round(alpha*180/math.pi)) + 
                '_' + liqName + '/'
                )

if os.path.isdir(caseDir):                                              #ensure, that the caseDir is clear
    sh.rmtree(caseDir)
    
sh.copytree(baseCase,caseDir)                                             #copy data to caseDir
    
#SPECIFY CURRENT SCRIPT VERSIONS========================================
blockMeshGen        = 'fblockMeshGen_rPFF'
inletBCWriter       = 'finletBCWriter_rPFF'
caseConstructor     = 'caseConstructor_rPFF'
rivuletPostProc     = 'rivuletPostProc_rPFF'
rivuletPostProc2Blender = 'rivuletPostProc2Blender_rPFF'
blenderPrep         = 'blenderPrep_rPFF'


#COPY CURRENT SCRIPT VERSIONS===========================================
scFolder= '/media/martin/Data_3/05_PlateDCases/00_Scripts/'             #folder with Scripts sources
scNames = [ blockMeshGen,                                               #preProcFunc - mesh gen.
            caseConstructor,                                            #copy current version of caseConstructor
            inletBCWriter,                                              #preProcFunc - BC writer
            rivuletPostProc,                                            #rivulet postprocessing (paraview)
            rivuletPostProc2Blender,                                    #export paraview->blender
            blenderPrep,                                                #rivulet postprocessing (blender)
            ]                                   
for scName in scNames:
    sh.copyfile(scFolder + scName + '.py',caseDir + scName + '.py')     #copy current script version
    
#CASE CONSTANTS AND CALCULATIONS========================================
# input data------------------------------------------------------------
# -- global parameters
g       = 9.81                                                          #grav. acc., m/s2
deltaWet= 1e-5                                                          #height above which is the plate considered wet, m

# -- liquid properties
[sigma,rho,mu,theta0,thetaA,thetaR] = dfluidData(liqName)
#~ [_,rhoA,muA,_,_,_]                  = dfluidData('AIR')
#~ NOTE: liquid properties are stored in a special dictionary
#~ sigma       ... surface tension coefficient of the liquid, N/m
#~ rho         ... density of the liquid, kg/m3
#~ mu          ... liquid dynamic viscosity, Pas
#~ theta0,thetaA,thetaR ... equilibrium, advancing and receding contact
#~                          angles

# -- further calculations
mDot    = Q0*rho                                                        #mass flow rate calculation
beta    = float((theta0+thetaA+thetaR)/3)/180*math.pi                   #get initial contact angle in radians

# -- additional parameters
lC      = math.sqrt(sigma/(rho*g));                                     #liquid capillary length

# prep calculations-----------------------------------------------------
#~ a0Gs    = (105*mu*Q0/(4*rho*g*math.tan(beta)**3))**0.25                   #inlet width - initial guess
# find inlet width
BFunc   = lambda a0 : a0*math.sqrt(rho*g*np.cos(alpha)/sigma)
#~ fFunc   = lambda Bsqrt : np.cosh(Bsqrt)
#~ fFunc   = lambda Bsqrt : np.divide(
    #~ 54*np.multiply(Bsqrt,np.cosh(Bsqrt)) + 
    #~ 6*np.multiply(Bsqrt,np.cosh(3*Bsqrt)) - 
    #~ 27*np.sinh(Bsqrt) - 
    #~ 11*np.sinh(3*Bsqrt),
    #~ np.multiply(36*np.power(Bsqrt,4),np.power(np.sinh(Bsqrt),3)))
#~ rFunc   = lambda a0 : mu*Q0/(np.power(a0,4)*rho*g*np.power(np.tan(beta),3)) - fFunc(BFunc(a0))
# test plot
#~ a0Vec = np.linspace(a0Gs/2, a0Gs*2, 301)
#~ plt.semilogy(a0Vec, rFunc(a0Vec))
#~ plt.xlabel("a0")
#~ plt.ylabel("expression value")
#~ plt.grid()
#~ plt.show()
#~ # fsolve function
#~ a0      = fsolve(rFunc,a0Gs, args=(), fprime=None, full_output=1, col_deriv=0, xtol=1e-4, maxfev=0, band=None, epsfcn=None, factor=10.0, diag=None)
#~ a0      = a0[0][0]
#~ a0      = a0Gs
#~ # find inlet height
#~ h0      = a0*math.tan(beta)*math.tanh(0.5*BFunc(a0))/BFunc(a0)

# find inlet dimensions (nasty)
QMax    = 11.29e-6
a0      = 4.2e-3                                                         #inlet width (hardcoded)
h0      = a0*math.tan(beta)*math.tanh(0.5*BFunc(a0))/BFunc(a0)
#~ h0      = math.sqrt(3)/4*a0#*Q0/QMax
#~ h0      = 4e-4


#OPEN AUTOGENERATED README FILE=========================================
README  = open(caseDir + './README','a')                                #open file to append
# -- start by writing basic case info
README.write('\ncaseDir:' + caseDir + '\n\n')
README.write('Q0        \t = \t ' + repr(round(Q0*1e6,4)) + ' mL/s\n')
README.write('alpha     \t = \t ' + repr(alpha/math.pi*180) + ' deg\n')
README.write('liqName   \t = \t ' + liqName + '\n')
README.write('a0        \t = \t ' + '%0.2e m\n'%a0)
README.write('h0        \t = \t ' + '%0.2e m\n'%h0)
README.write('beta0     \t = \t ' + '%0.2e deg\n'%(beta*180/math.pi))
README.write('nCores    \t = \t ' + repr(nCores) + '\n')
README.write('startTime \t = \t ' + repr(startTime) + ' s\n')
README.write('endTime   \t = \t ' + repr(endTime) + ' s\n')

#BLOCKMESHDICT FILE GENERATION==========================================

#-----------------------------------------------------------------------
# GEOMETRY DATA
#-----------------------------------------------------------------------
# geometry arguments (all in [m])
cellW   = 0.150                                                         #exp. cell width
cellL   = 0.300                                                         #exp. cell length
#-----------------------------------------------------------------------
# MESH DATA
#-----------------------------------------------------------------------
# number of cells in each direction for each part of the mesh
nCellsW  = 300  #number of cells in width direction
nCellsL  = 600  #number of cells in length direction
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
fblockMeshGen(caseDir,a0,h0,cellW,cellL,nCellsW,nCellsL,mScale)
print 'DONE=======================================\n\n'
#BC FILES MODIFICATION==================================================
#-----------------------------------------------------------------------
# FUNCTION CALL
#-----------------------------------------------------------------------
print 'ADJUSTING BC===============================\n\n'
finletBCWriter(caseDir,a0,h0,mDot,alpha,liqName,cellW,cellL,nCellsW,nCellsL)
print 'DONE=======================================\n\n'
#CONSTANTS DIRECTORY FILES MODIFICATIONS================================
print 'ADJUSTING FILES IN ./CONSTANTS=============\n\n'
#-----------------------------------------------------------------------
# additionalControls
#-----------------------------------------------------------------------
#
# changeable: solvePrimaryRegion false; // true;
#
with open(caseDir + './constant/additionalControls', 'r') as file:
    # read a list of lines into data
    data = file.readlines()
    
idStr   = 'solvePrimaryRegion'
isSolve = 'false'

for i in range(len(data)):
    if data[i].find(idStr)>-1:
        data[i] = (idStr + '\t' + isSolve + ';\n\n')

with open(caseDir + './constant/additionalControls', 'w') as file:
    file.writelines( data )

#-----------------------------------------------------------------------
# surfaceFilmProperties
#-----------------------------------------------------------------------
#
# defines physical properties for liquid film
#

# general properties
specieName = [liqName]                                                    #all as strings -> easier coding
rho0       = [repr(rho)]                                                  #density, kg/m3
mu0        = [repr(mu)]                                                   #viscosity, Pas
sigma0     = [repr(sigma)]                                                #s. tension coef., N/m

# three phase line
deltaWet   = [repr(deltaWet)]
beta       = [repr(theta0)]
minValue   = [repr(thetaR),repr(lC/10)]
maxValue   = [repr(thetaA),repr(5*lC)]
expectation= [repr(theta0)]
variance   = [repr(theta0/2)]

idStr = ['specieName','rho0','mu0','sigma0','deltaWet','minValue',                 #v2.3.1
         'maxValue','expectation','variance']
         
pVals = [specieName,rho0,mu0,sigma0,deltaWet,minValue,maxValue,expectation,variance]

# write everything to the file
with open(caseDir + './constant/surfaceFilmProperties', 'r') as file:
    # read a list of lines into data
    data = file.readlines()
            
for j in range(len(idStr)):
    k = 0
    for i in range(len(data)):
        fInd = data[i].find(idStr[j])
        if fInd>-1:
            data[i] = data[i][:fInd] + idStr[j] + '\t' + pVals[j][k] + ';\n'
            k = k+1   

with open(caseDir + './constant/surfaceFilmProperties', 'w') as file:
    file.writelines( data )

#-----------------------------------------------------------------------
# g
#-----------------------------------------------------------------------
#
# defines gravitational acceleration (prepared for inclined plate)
#

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
    
print 'DONE=======================================\n\n'   
#SYSTEM DIRECTORY FILES MODIFICATIONS===================================
print 'ADJUSTING FILES IN ./SYSTEM================\n\n'
#~ #-----------------------------------------------------------------------
#~ # setFieldsDict
#~ #-----------------------------------------------------------------------
#~ #
#~ # creates initial condition for the case (presence of the liquid)
#~ #
#~ 
#~ # set up the cylinder with liquid in it
#~ aCyl = a0/2
#~ rCyl = a0/eps+h0
#~ 
#~ idStr1 = ['p1 (0',
         #~ 'p2 (0',
         #~ 'radius ']      
         #~ 
#~ idStr2 = [' deltaf ']         
#~ 
#~ pVals1 = [repr(-0.5*aCyl) + '\t0)',repr(0.5*aCyl) + '\t0)' ,repr(rCyl)]
#~ pVals2 = [repr(0*float(deltaWet[0]))]
#~ 
#~ # write everything to the file
#~ with open(caseDir + './system/wallFilmRegion/setFieldsDict', 'r') as file:
    #~ # read a list of lines into data
    #~ data = file.readlines()
    #~ 
#~ for j in range(len(idStr1)):
    #~ for i in range(len(data)):
        #~ fInd = data[i].find(idStr1[j])
        #~ if fInd>-1:
            #~ data[i] = data[i][:fInd] + idStr1[j] + '\t' + pVals1[j] + ';\n'
            #~ 
#~ for j in range(len(idStr2)):
    #~ for i in range(len(data)):
        #~ fInd = data[i].find(idStr2[j])
        #~ if fInd>-1:
            #~ data[i] = data[i][:fInd] + idStr2[j] + '\t' + pVals2[j] + '\n'          
#~ 
#~ with open(caseDir + './system/wallFilmRegion/setFieldsDict', 'w') as file:
    #~ file.writelines( data )
    
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
with open(caseDir + './system/wallFilmRegion/decomposeParDict', 'r') as file:
    # read a list of lines into data
    data = file.readlines()
    
for j in range(len(idStr)):
    for i in range(len(data)):
        fInd = data[i].find(idStr[j])
        if fInd>-1:
            data[i] = data[i][:fInd] + idStr[j] + '\t' + pVals[j] + ';\n'

with open(caseDir + './system/decomposeParDict', 'w') as file:
    file.writelines( data )
    
with open(caseDir + './system/decomposeParDict', 'r') as file:
    # read a list of lines into data
    data = file.readlines()
    
for j in range(len(idStr)):
    for i in range(len(data)):
        fInd = data[i].find(idStr[j])
        if fInd>-1:
            data[i] = data[i][:fInd] + idStr[j] + '\t' + pVals[j] + ';\n'

with open(caseDir + './system/wallFilmRegion/decomposeParDict', 'w') as file:
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
            '#PBS -q paralel',
            '#PBS -l nodes=1:ppn=',
            'caseDir=',
            ]

caseName = (
            'rPFF_' + 
            repr(round(Q0*1e6,4)) + '_' + repr(round(alpha*180/math.pi)) + 
            '_' + liqName
            )

pVals = [caseName+'.pbs',repr(nCores),repr(nCores),"'" + caseName + "'"]

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
# rivuletPostProc_rPFF.py
#-----------------------------------------------------------------------
#
# defines cylinder slice filter -> filter radius has to be changed
#
README.write('\n' + rivuletPostProc + '.py\n')

idStr = ['mu0     =','gamma0  =','rho0    =','Q0      =',
         #~ 'a0      =','h0      =','eps     =',
         'alpha0  ='
         ]
wrStr = [("%4.2e" % (mu)),
         ("%4.2e" % (sigma)),
         ("%4.2e" % (rho)),
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
# blenderPrep_rPFF.py
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

#~ print 'DONE=======================================\n\n'
#CLOSE THE AUTOGENERATED README FILE====================================
README.write('// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * // \n\n')
README.close()
