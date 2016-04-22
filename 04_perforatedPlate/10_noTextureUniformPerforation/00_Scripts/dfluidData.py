#!/usr/bin/python

#FILE DESCRIPTION=======================================================
#~ 
    #~ [sigma,rho,mu,theta0,thetaA,thetaR] = dfluidData(liqName)
#~ 
#~ DICTIONARY which returns fluidData for the selected liquid type
#~ INPUT
#~ liqName     ... name of the liquid, must be in database
#~ 
#~ OUTPUT
#~ sigma       ... surface tension coefficient of the liquid, N/m
#~ rho         ... density of the liquid, kg/m3
#~ mu          ... liquid dynamic viscosity, Pas
#~ theta0,thetaA,thetaR ... equilibrium, advancing and receding contact
#~                          angles

#LICENSE================================================================
#  dfluidData.py
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

def dfluidData(liqName):
    return {
        'DC05'  : [17.57e-3,920.0,5.073e-3,5.0,10.0,0.0],               #silicon oil
        'DC10'  : [17.89e-3,940.0,10.419e-3,5.0,10.0,0.0],              #silicon oil
        'H2O'   : [55.18e-3,998.0,1.178e-3,60,70,50],                   #water (Freiberg)
        'H2OCk' : [72.80e-3,997.0,8.899e-4,70,75,65],                   #water (Cooke et al. 2012)
        'SURF'  : [29.36e-3,998.0,1.114e-3,0.0,0.0,0.0],                #water with surfactants
        'AIR'   : [0,1.184,18.408e-6,0.0,0.0,0.0],                      #air at 25 deg C
    }.get(liqName,'DC10')
