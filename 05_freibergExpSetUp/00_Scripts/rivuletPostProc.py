#!/usr/bin/python

#FILE DESCRIPTION=======================================================
#~ Python script used for post-processing automatization of the rivulet
#~ flow down the experimental plate in Freiberg
#~
#~ NOTES:
    #~ - before running, the main file has to be highlighted
    #~ - can be ran from command line 
    #~ - still unfinished BUT improvement
    
#~ USAGE:
   #~ paraFoam --script=./rivuletPostProc.py 


#LICENSE================================================================
#  rivuletProstProc.py
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

# PARAMETERS============================================================
xAll = 0.025
ySkip= 0.07

# POSTPROCESSING INITIATION=============================================
#~ try: paraview.simple
#~ except: from paraview.simple import *
import math
import glob

mainCase = glob.glob('./*.OpenFOAM')                                     #works only for the cases with 1 foam file

paraview.simple._DisableFirstRenderCameraReset()

activeSource_OpenFOAM = GetActiveSource()

# enable all available fields
activeSource_OpenFOAM.VolumeFields = ['alpha.liquid', 'p_rgh', 'U']

# show all for internal mesh
activeSource_OpenFOAM.MeshParts = ['internalMesh']

# I dont want to see the main mesh / I do want to see it as transparent wireframe
allIntMeshRepresentation = GetDisplayProperties( activeSource_OpenFOAM )
allIntMeshRepresentation.Visibility = 1
allIntMeshRepresentation.Representation = 'Wireframe'
allIntMeshRepresentation.Opacity = 0.1

# set up black background (seems prettier)
RenderView1 = GetRenderView()
RenderView1.UseTexturedBackground = 0
RenderView1.Background = [0.0, 0.0, 0.0]

Render()

activeSource_OpenFOAM = FindSource( mainCase[0] )

# GO TO THE ANIMATION (TIME RANGE) END==================================
AnimationScene1 = GetAnimationScene()
AnimationScene1.GoToLast()
Render()

# CREATE A SCALAR CLIP - SHOW ONLY THE RIVULET==========================
liqOnly = Clip( ClipType="Scalar" )

liqOnly.Scalars = ['POINTS', 'alpha.liquid']
#~ liqOnly.ClipType.Origin = [0.022136231884360313, 0.0, 0.0]
liqOnly.Value = 0.5

liqOnlyRepresentation = Show()

liqOnlyRepresentation.Opacity = 1.0

source = GetActiveSource()

#~ data = source.GetCellDataInformation()
data = source.GetPointDataInformation()

#get the array and the respective min-max
array = data.GetArray('U')
dataRange = array.GetRange(-1)                                          #-1 for magnitude

# SCALAR BAR============================================================

a3_U_PVLookupTable = GetLookupTableForArray( "U", 3,
    RGBPoints=[0.0, 0.0, 0.0, 1.0, dataRange[1], 1.0, 0.0, 0.0],
    VectorMode='Magnitude',
    ScalarRangeInitialized=1.0 )

a3_U_PiecewiseFunction = CreatePiecewiseFunction( Points=[0.0, 0.0, 0.5, 0.0, 1.0, 1.0, 0.5, 0.0] )

liqOnlyRepresentation.Representation = 'Surface'
liqOnlyRepresentation.ColorArrayName = ('POINT_DATA', 'U')
liqOnlyRepresentation.LookupTable = a3_U_PVLookupTable

a3_U_PVLookupTable.ScalarOpacityFunction = a3_U_PiecewiseFunction
        
Render()

ScalarBarWidgetRepresentation = CreateScalarBar( Title='$\|u\|,[\mathrm{ms^{-1}}]$',
 ComponentTitle='',
 LabelFontSize=12,
 Enabled=1,
 LookupTable=a3_U_PVLookupTable,
 TitleFontSize=14,
 LabelFormat='$%-#5.2e$')
RenderView1.Representations.append(ScalarBarWidgetRepresentation)

Render()

# ADD CASE TITLE========================================================
caseTitle = Text()

caseTitleRepresentation = Show()

caseTitle.Text = 'Rivulet flow down an inclined plate'

caseTitleRepresentation.Bold = 1
caseTitleRepresentation.Position = [xAll,0.90]

Render()

# ADD CASE DESCRIPTION==================================================
# Note: this is a major pain in the ass, but paraview cannot process
#       multilines latex entries

idStr = [   '$\\nu\,\,= ',
            '$\\gamma\,\,=',
            '$\\varrho\,\,=',
            '$Q_0=',
            #~ '$a_0\,=',
            #~ '$h_0\,=',
            #~ '$\\varepsilon\,\,\,=',
            '$\\alpha\,\,=',
            ]
         
nu0     =	[1.18e-06, 1.55e-05]
gamma0  =	5.52e-02
rho0    =	[9.98e+02, 1.18e+00]
Q0      =	3.03e-06
alpha0  =   60
#~ a0      =	1.70e-02
#~ h0      =	4.26e-04
#~ eps     =	1.00e-02
         
valStr = [("[%s]" % ', '.join(("%4.2e" % (e)) for e in nu0)  + '\,\mathrm{m^2s^{-1}}'),
          ("%4.2e" % (gamma0)   + '\,\mathrm{N\,m^{-1}}'),
          ("[%s]" % ', '.join(("%4.2f" % (e)) for e in rho0) + '\,\mathrm{kg\,m^{-3}}'),
          ("%4.2e" % (Q0)       + '\,\,\mathrm{m^{3}s^{-1}}'),
          #~ ("%4.2e" % (a0)       + '\,\mathrm{m}'),
          #~ ("%4.2e" % (h0)       + '\,\mathrm{m}'),
          #~ ("%4.2e" % (eps)      + '\,-'),
          ("%4.0f" % (alpha0)       + '\mathrm{^\circ{}}'),
          ]
         
caseDesc = []
caseDescRepresentation = []

for i in range(len(idStr)):
    caseDesc.append(Text())
    caseDescRepresentation.append(Show())
    
    caseDesc[i].Text = (idStr[i] + '\t' + valStr[i]) + '$'
    
    caseDescRepresentation[i].FontFamily = 'Courier'
    caseDescRepresentation[i].FontSize = 16
    caseDescRepresentation[i].Position = [xAll, 0.7-i*ySkip]

    Render()
#~ 
# ADD ANOTATE TIME SOURCE===============================================
annotTime = AnnotateTime()

annotTimeRepresentation = Show()

annotTime.Format = '$\mathrm{Time:\,%5.2f\,s}$'

annotTimeRepresentation.FontFamily = 'Courier'
annotTimeRepresentation.Position = [xAll, 0.025]
annotTimeRepresentation.Visibility = 1

Render()

# POST RUNNING MODIFICATIONS============================================

# try to rescale the colors for deltaf
AnimationScene1 = GetAnimationScene()
AnimationScene1.GoToLast()

Render()

# camera position

ResetCamera()
RenderView1 = GetRenderView()
RenderView1.CameraViewUp = [-0.8, -0.5, 0]
RenderView1.CameraFocalPoint = [0.15,-0.1,0]                               #center of the plate
RenderView1.CameraClippingRange = [5, 5]                                #who knows what it does...
RenderView1.CameraPosition = [0.2,0.15,0.2]

Render()



