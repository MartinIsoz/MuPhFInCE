#!/usr/bin/python

#FILE DESCRIPTION=======================================================
#~ Simple python script to enable some parametrization of the mesh
#~ created for the case of rivulet flow down an inclined plate
#~


#LICENSE================================================================
#  blockMeshGenCyl_rPFF.py
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
def finletBCWriter(caseDir,												#need to specify case directory
    a0=0.01,h0=0.001,mDot=1e-3,alpha=1,
    liqName='DC10',
    cellW=0.150,cellL=0.300,
    nCellsW=150,nCellsL=300):
    
    #IMPORT BLOCK=======================================================
    import os
    import math
    from dfluidData import dfluidData
    #
    #GET THE DATA=======================================================
    #===================================================================
    #                           EDITABLE
    #===================================================================    
    g   = 9.81
    [sigma,rho,mu,theta0,thetaA,thetaR] = dfluidData(liqName)
    beta = float((theta0+thetaA+thetaR)/3)/180*math.pi                #get initial contact angle in radians
    #===================================================================
    #                           DO NOT EDIT
    #===================================================================
    
    # recalculation for ND mesh - lenght is ND by inlet height
    L             = 1#h0
    a0,h0,cellL,cellW = a0/L,h0/L,cellL/L,cellW/L
    
    # auxiliary variables - meshing
    nCellsIn   = int(round(a0/cellW*nCellsW)+round(a0/cellW*nCellsW)%2)
    nCellsWVec = [(nCellsW-nCellsIn)/2,nCellsIn,(nCellsW-nCellsIn)/2]
    
    hVec = []
    uVec = []
    #~ for i in range(0,nCellsIn/2):
         #~ hVec.append(a0**2 - (2*i*a0/nCellsIn)**2)
    #~ for i in range(nCellsIn/2+1,nCellsIn)
         #~ hVec.append(a0**2 - (2*i*a0/nCellsIn)**2)
    Bsqrt = a0*math.sqrt(rho*g*math.cos(alpha)/sigma)
    A     = a0*math.tan(beta)/(Bsqrt*math.sinh(Bsqrt))
    
    #~ yVec  = [(2*a0*i/float(nCellsIn) - a0) for i in range(nCellsIn+1)]
    #~ print yVec
    
    print 'sqrt(B) = ' + repr(Bsqrt)
    #~ print A
    
    # calculate the inlet profile shape
    for i in range(nCellsIn+1):
        dzeta = 2*i/float(nCellsIn) - 1
        hVec.append(A*(math.cosh(Bsqrt)-math.cosh(Bsqrt*dzeta)))
    
    #calculate the inlet profile cross section
    step    = 2*a0/float(nCellsIn)
    cSec    = 0
    for i in range(len(hVec)-1):
        cSec = cSec + hVec[i+1] + hVec[i]
    cSec    = cSec*step/2
    
    #calculate the inlet liquid velocity to sustain demanded mDot
    u0      = mDot/rho/cSec
    
    #~ for i in range(len(hVec)):
        #~ uVec.append([hVec[i]**2*rho*g/(2*mu),0,0])
    #~ print uVec
    
    
    #=======================================================================
    
    #=======================================================================
    #CREATE FILE AND WRITE THE DATA IN======================================
    idStr = 'inlet'
    
    # write everything to the file
    # Uf
    with open(caseDir + '0.org/wallFilmRegion/Uf', 'r') as file:
        # read a list of lines into data
        data = file.readlines()
    
    for i in range(len(data)):
        fInd = data[i].find(idStr)
        if fInd>-1:
            data[i:] = []
            break
    
    with open(caseDir + '0.org/wallFilmRegion/Uf', 'w') as file:
        file.writelines( data )
    
    
    bMD = open(caseDir + '0.org/wallFilmRegion/Uf','a')                                                 #open file temporary file for writing
    #-----------------------------------------------------------------------
    # write data to file
    # -- case of dirichlet boundary
    #~ bMD.write('\tinlet \n\t{ \n')
    #~ bMD.write('\t\ttype\tfixedValue;\n')
    #~ bMD.write('\t\tvalue\tnonuniform List<vector>  \n\t\t' + repr(nCellsIn) + '\n\t\t(\n')
    #~ for row in uVec:
        #~ bMD.write('\t\t\t ( ' + ' '.join(str(e) for e in row) + ' )\n')
    #~ bMD.write('\t\t); \n')
    #~ bMD.write('\t} \n\n')
    #~ bMD.write('}\n\n')
    # -- case of flowRateInletVelocity (could it be applied?)
    #~ bMD.write('\tinlet \n\t{ \n')
    #~ bMD.write('\t\ttype\tflowRateInletVelocity;\n')
    #~ bMD.write('\t\tmassFlowRate\tconstant\t' + repr(mDot) + ';\n')
    #~ bMD.write('\t\tvalue\t\tuniform (1 0 0);\n')
    #~ bMD.write('\t} \n\n')
    #~ bMD.write('}\n\n')
    # -- case of constant velocity
    bMD.write('\tinlet \n\t{ \n')
    bMD.write('\t\ttype\tfixedValue;\n')
    bMD.write('\t\tvalue\tuniform \t\t(%5.4e 0 0);\n'%u0)
    bMD.write('\t} \n\n')
    bMD.write('}\n\n')
    
    
    #-----------------------------------------------------------------------
    # footline
    bMD.write('// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * // \n\n')
    
    #-----------------------------------------------------------------------
    # close file
    bMD.close()
    
    # deltaf
    with open(caseDir + '0.org/wallFilmRegion/deltaf', 'r') as file:
        # read a list of lines into data
        data = file.readlines()
    
    for i in range(len(data)):
        fInd = data[i].find(idStr)
        if fInd>-1:
            data[i:] = []
            break
    
    with open(caseDir + '0.org/wallFilmRegion/deltaf', 'w') as file:
        file.writelines( data )
    
    
    bMD = open(caseDir + '0.org/wallFilmRegion/deltaf','a')                                                 #open file temporary file for writing
    #-----------------------------------------------------------------------
    # write data to file
    bMD.write('\tinlet \n\t{ \n')
    bMD.write('\t\ttype\tfixedValue;\n')
    bMD.write('\t\tvalue\tnonuniform List<scalar>  \n\t\t' + repr(nCellsIn+1) + '\n\t\t(\n')
    for i in range(len(hVec)):
        bMD.write('\t\t\t ' + repr(hVec[i]) + '\n')
    bMD.write('\t\t); \n')
    bMD.write('\t} \n\n')
    bMD.write('}\n\n')
    #~ bMD.write('\tinlet \n\t{ \n')
    #~ bMD.write('\t\ttype\tfixedValue;\n')
    #~ bMD.write('\t\tvalue\tuniform \t\t' + repr(h0) + ';\n')
    #~ bMD.write('\t} \n\n')
    #~ bMD.write('}\n\n')
    
    
    #-----------------------------------------------------------------------
    # footline
    bMD.write('// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * // \n\n')
    
    #-----------------------------------------------------------------------
    # close file
    bMD.close()
    
    return;
    
