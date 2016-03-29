#!/usr/bin/python

#FILE DESCRIPTION=======================================================

#  Python function used to prepare initial condition for the rivulet
#  spreading CFD.
#
#  Based on the surrogate model proposed by ISOZ in [1]
#
#  Script rewrites setFieldsDict in order to create an initial guess
#  for the rivulet shape
#
#  Script should be usable for DC05 and DC10 liquids (at low flow rates).
#  For the case of higher flow rates, the model is not yet derived, for
#  water, a different model (Towell and Rothfeld, [2]) should be
#  implemented
#
# MODEL DESCRIPTION:
#  - gravity affects the speed of movement of \tau along the plate
#  - gravity does not have any effect on the profile shape and speed of
#    spreading
#  - at the time, model writes only the shape of GLI but not the
#    corresponding velocity field (I do not know how to implement it
#    via setFieldsDict - there might be a possibility to use
#    funkySetFields utility but I did not look into it yet)
#
# NOTES:
#  - from the setFieldsDict point of view, the interface (rivulet) is
#    reconstructed by a series of cylinders
#  - control the implementation !! (and as a matter of fact, also the
#    model
#  - the used model uses the member tan(beta) directly - it should be
#    better suitable for the case of higher contact angles BUT its
#    usability is still limited because of the assumptions used
#    throughout its derivation
#  - prepares also the inlet part of the geometry (based on an
#    approximated empirical model
#
# USAGE:
#  - it is a function callable by caseConstructor


#LICENSE================================================================
#  fprepIC_noGravity.py
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

def fprepIC_noGravity(caseDir,                                          #case directory name
            a0,Q0,                                                      #initial conditions
            liqName,l,                                                  #model defining properties
            alpha,L,nCellsX,H,nCellsZ,                                  #geometrical and meshing parameters
            pltFlag,                                                    #output plots
        ):
    #IMPORT BLOCK=======================================================
    import math
    import numpy as np
    #~ from scipy.optimize import fsolve                                   #NAE solver
    from scipy.integrate import odeint                                      #ODE solver
    import matplotlib.pyplot as plt
    
    #IMPORT BLOCK-CUSTOM================================================
    from dfluidData import dfluidData
    
    #LOCAL FUNCTIONS====================================================
    def writeCylinder(h,a,x,deltaX):
        # function returning list o strings to write cylinderToCell entry
        # into setFieldsDict file
        R   = h/2.0 + a**2.0/(2.0*h)                                    #cylinder diameter
        d   = R - h                                                     #how much bellow the plate is the cylinder center
        
        # -- create the strings to return
        cellStr = []
        cellStr.append('\tcylinderToCell\n\t\t{\n')                     #entry openning lines
        
        cellStr.append('\t\t\tp1 (%5.5e %5.5e %5.5e);\n'%(x,0.0,-d))
        cellStr.append('\t\t\tp2 (%5.5e %5.5e %5.5e);\n'%(x+deltaX,0.0,-d))
        cellStr.append('\t\t\tradius %5.5e;\n\n'%R)
        
        cellStr.append('\t\t\tfieldValues\n\t\t\t(\n')
        cellStr.append('\t\t\t\tvolScalarFieldValue alpha.liquid 1\n\t\t\t);\n')
        
        cellStr.append('\t\t}\n')                                       #entry ending line
            
        return cellStr
        
    def writeBox(h,deltah,a,x,deltaX,UVec,p_rgh):
        # function returning list of strings to write boxToCell entry into
        # setFieldsDict file
        
        cellStr = []
        cellStr.append('\tboxToCell\n\t\t{\n')                              #entry openning lines
        
        cellStr.append('\t\t\tbox (%5.5e %5.5e %5.5e) (%5.5e %5.5e %5.5e);\n\n'%(x,-a,h,x+deltaX,a,h+deltah))
        
        cellStr.append('\t\t\tfieldValues\n\t\t\t(\n')
        cellStr.append('\t\t\t\tvolVectorFieldValue U (%5.5e %5.5e %5.5e)\n'%tuple(UVec))
        cellStr.append('\t\t\t\tvolScalarFieldValue p_rgh %5.5e\n\t\t\t);\n'%p_rgh)
        
        cellStr.append('\t\t}\n')                                           #entry ending line
        
        return cellStr
        
    def writeBoxAlpha(h,deltah,a,x,deltaX,alpha):
        # function returning list of strings to write boxToCell entry into
        # setFieldsDict file
        
        cellStr = []
        cellStr.append('\tboxToCell\n\t\t{\n')                              #entry openning lines
        
        cellStr.append('\t\t\tbox (%5.5e %5.5e %5.5e) (%5.5e %5.5e %5.5e);\n\n'%(x,-a,h,x+deltaX,a,h+deltah))
        
        cellStr.append('\t\t\tfieldValues\n\t\t\t(\n')
        cellStr.append('\t\t\t\tvolScalarFieldValue alpha.liquid %5.5e\n\t\t\t);\n'%alpha)
        
        cellStr.append('\t\t}\n')                                           #entry ending line
        
        return cellStr
        
    def writeRotBoxAlpha(origin,i,j,k,alpha):
        # function returning list of strings to write boxToCell entry into
        # setFieldsDict file
        
        cellStr = []
        cellStr.append('\trotatedBoxToCell\n\t\t{\n')                              #entry openning lines
        
        cellStr.append('\t\t\torigin (%5.5e %5.5e %5.5e);\n'%tuple(origin))
        cellStr.append('\t\t\ti (%5.5e %5.5e %5.5e);\n'%tuple(i))
        cellStr.append('\t\t\tj (%5.5e %5.5e %5.5e);\n'%tuple(j))
        cellStr.append('\t\t\tk (%5.5e %5.5e %5.5e);\n\n'%tuple(k))
        
        cellStr.append('\t\t\tfieldValues\n\t\t\t(\n')
        cellStr.append('\t\t\t\tvolScalarFieldValue alpha.liquid %5.5e\n\t\t\t);\n'%alpha)
        
        cellStr.append('\t\t}\n')                                           #entry ending line
        
        return cellStr

    ##CONSTANTS=========================================================
    # -- other physical properties
    g       = 9.81                                                      #gravity
    
    # -- liquid properties
    [sigma,rho,mu,theta0,thetaA,thetaR] = dfluidData(liqName)
    
    # -- calculation parameters
    deltaX  = L/nCellsX
    deltaZ  = H/nCellsZ
    
    #MODEL DEFINITION=======================================================
    # -- constants
    psi     = np.power(105.0*mu*Q0 / (4.0*rho*g*np.sin(alpha)),0.3333)
    varpi   = 2.0*mu/(rho*g*np.sin(alpha)*l**2.0)
    
    # -- functions
    betaFunc= lambda a      : np.arctan(np.divide(psi,a**1.3333))
    h0Func  = lambda a,beta : 2.0*np.multiply(a,np.tan(beta)/2.0)
    
    # -- model ODE (to be solved numerically)
    def model(a,x):
        beta = betaFunc(a)
        dadx = 1.0*beta**3.0*sigma*varpi/(9.0*mu*np.log(a/(2.0*np.exp(2.0)*l)))
        return dadx
        
    def jac(a,x):
        dfun = -(1.0/9.0)*np.arctan(psi/a**4.0)**2.0*sigma*(np.arctan(psi/a**4.0)*(a**8.0+psi**2.0)-12.0*a**4.0*psi*(ln(2.0)+2.0-ln(a/l)))*varpi/(mu*(ln(2.0)+2.0-ln(a/l))**2.0*(a**8.0+psi**2.0)*a)
        return dfun
    
    #SETFIELDSDICT EDITING==============================================
    with open(caseDir + './system/setFieldsDict', 'r') as file:
        # read a list of lines into data
        data = file.readlines()
        
    regsLine = 0                                                        #at the time empty
        
    # -- find position of regions keyword
    for i in range(len(data)):
        if data[i].find('regions') >-1:
            auxData = data[0:i+2]
            regsLine = i
            break
            
    # -- find the height of liquid surface at inlet
    h       = 2.0*math.pi/(5.0*alpha)*(6.0*Q0**2.0/g)**0.2
    a0      = 2.0*h*np.sqrt(3.0)/3.0
            
    # -- fill in the inlet by liquid
    auxData.extend(writeRotBoxAlpha([-h,-10,0],[-10/np.tan(alpha),0,-10],[0,20,0],[10,0,-10/np.tan(alpha)],1.0))
    
    #~ # -- connect the liquid in inlet with the liquid in rivulet
    #~ auxData.extend(writeRotBoxAlpha([0,-a0,h],[-10*np.tan(alpha),0,-10],[0,2*a0,0],[10,0,-10*np.tan(alpha)],1.0))
    
    # -- solve the model ODE
    x       = np.linspace(-h,L,nCellsX+int(round(nCellsX*h/L))+1)       #create solution grid
    aList   = odeint(model,a0,x,Dfun=jac,printmessg=True)               #solve the system
    
    # -- auxiliary calculations
    betaList = betaFunc(aList)
    h0List   = h0Func(aList,betaList)
            
    # -- extend the list by the cylinders (gas-liquid interface position)
    for i in range(nCellsX):
        # -- prepare the phase fraction fields
        cellStr = writeCylinder(h0List[i],aList[i],x.item(i),deltaX)
        auxData.extend(cellStr)
        # -- prepare the velocity field - as boxes
        R = h0List.item(i)/2.0 + aList.item(i)**2.0/(2.0*h0List.item(i))
        for j in range(1,int(math.ceil(nCellsZ*h0List.item(i)/H))):
            uVec    = [rho*g*np.sin(alpha)/(2.0*mu)*(2.0*h0List.item(i)*j*deltaZ - (j*deltaZ)**2.0),0.0,0.0]
            #~ p_rgh   = rho*g*np.cos(alpha)*(h0List.item(i) - (j*deltaZ)) + np.tan(betaList.item(i))/aList.item(i)*sigma
            p_rgh   = np.tan(betaList.item(i))/aList.item(i)*sigma
            # -- get the current rivulet width (at height j*deltaZ)
            c       = np.sqrt((R-(h0List.item(i)-j*deltaZ)/2.0)*8.0*(h0List.item(i)-j*deltaZ))
            cellStr = writeBox(j*deltaZ,deltaZ,c,x.item(i),deltaX,uVec,p_rgh)
            auxData.extend(cellStr)
        
    # -- extend the list by the rest of the lines
    auxData.extend(data[regsLine+2::])
    
    # rewrite the setFieldsDict file
    with open(caseDir + './system/setFieldsDict', 'w') as file:
        file.writelines( auxData )
        
    # PLOTTING THE CHARACTERISTICS OF PRESET SOLUTION===================
    if pltFlag:
        plt.figure(num=None, figsize=(20, 12), dpi=80, facecolor='w', edgecolor='k')
        plt.show(block=False)
        
        plt.subplot(2,1,1)
        plt.plot(betaList,'bo')
        plt.title('Contact angle evolution along the rivulet')
        plt.xlabel('step count')
        plt.xlim(0,len(betaList))
        plt.ylabel('apparent contact angle')
        
        plt.subplot(2,2,3)
        plt.plot(aList,'mo')
        plt.title('Rivulet half width evolution')
        plt.xlabel('step count')
        plt.xlim(0,len(aList))
        plt.ylabel('rivulet half width')
        
        plt.subplot(2,2,4)
        plt.plot(h0List,'co')
        plt.title('Rivulet centerline height evolution')
        plt.xlabel('step count')
        plt.xlim(0,len(h0List))
        plt.ylabel('rivulet centerline height')
        
        plt.show()








