#!/usr/bin/python

#FILE DESCRIPTION=======================================================
#~ Python script used for post-processing automatization of flow on an
#~ inclined (?textured?) plate (minimal postprocessing to test the results)
#~
#~ NOTES:
    #~ - still unfinished BUT improvement
    
#~ USAGE:
   #~ paraFoam --script=./postProcMinimal.py 


#LICENSE================================================================
#  prostProcMinimal.py
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
allIntMeshRepresentation.Visibility = 0
allIntMeshRepresentation.Representation = 'Wireframe'
allIntMeshRepresentation.Opacity = 0.1

# set up black background (seems prettier)
RenderView1 = GetRenderView()
RenderView1.UseTexturedBackground = 0
RenderView1.Background = [0.0, 0.0, 0.0]

activeSource_OpenFOAM = FindSource( mainCase[0] )

# CREATE A SCALAR CLIP - SHOW ONLY THE RIVULET==========================
liqOnly = Clip( ClipType="Scalar", guiName="liqOnly" )

liqOnly.Scalars = ['POINTS', 'alpha.liquid']
liqOnly.Value = 0.5

liqOnlyRepresentation = Show()

liqOnlyRepresentation.Representation = 'Surface'
liqOnlyRepresentation.Visibility = 0

# COLOR THE FILM BY FILM THICKNESS (CALCULATOR+PROPER COLORING)=========
fThCalc  = Calculator( guiName="fThCalc" )

fThCalc.Function = 'coordsZ'
fThCalc.ResultArrayName = 'hFun'

fThCalcRepresentation = Show()
fThCalcRepresentation.Visibility = 1

# SCALAR BAR============================================================

# ADD CASE TITLE========================================================

# ADD ANOTATE TIME SOURCE===============================================
annotTime = AnnotateTime()

annotTimeRepresentation = Show()

annotTime.Format = '$\mathrm{Time:\,%5.2f\,s}$'

annotTimeRepresentation.FontFamily = 'Courier'
annotTimeRepresentation.Position = [xAll, 0.025]
annotTimeRepresentation.Visibility = 1

Render()

# POST RUNNING MODIFICATIONS============================================

AnimationScene1 = GetAnimationScene()
AnimationScene1.GoToLast()

Render()

# SCALAR BAR============================================================
source = fThCalc                                                        #where to get the data

data = source.GetPointDataInformation()

#get the array and the respective min-max
array = data.GetArray('hFun')
dataRange = array.GetRange(0)                                          #-1 for magnitude

colorObjectRepresentation = fThCalcRepresentation                       #what object will be colored

a0_hFun_PVLookupTable = GetLookupTableForArray( "hFun", 0,
    #~ RGBPoints=[0.0, 0.0, 0.0, 0.0, dataRange[1], 1.0, 1.0, 1.0],     #grayscale coloring
    #~ ColorSpace='RGB',
    RGBPoints=[0.0, 0.0, 0.0, 1.0, dataRange[1], 1.0, 0.0, 0.0],        #classical rainbow coloring
    ColorSpace='HSV',
    ScalarRangeInitialized=1.0 )

a0_hFun_PiecewiseFunction = CreatePiecewiseFunction( Points=[0.0, 0.0, 0.5, 0.0, 1.0, 1.0, 0.5, 0.0] )

colorObjectRepresentation.Representation = 'Surface'
colorObjectRepresentation.ColorArrayName = ('POINT_DATA', 'hFun')
colorObjectRepresentation.LookupTable = a0_hFun_PVLookupTable

a0_hFun_PVLookupTable.ScalarOpacityFunction = a0_hFun_PiecewiseFunction
        
Render()

ScalarBarWidgetRepresentation = CreateScalarBar( Title='$h(x,y),[\mathrm{m}]$',
 ComponentTitle         =   '',
 LabelFontSize          =   12,
 Enabled                =   1,
 LookupTable            =   a0_hFun_PVLookupTable,
 TitleFontSize          =   14,
 AutomaticLabelFormat   =   0,
 LabelFormat            =   '$%-#5.2e$',
 RangeLabelFormat       =   '$%-#5.2e$',
 )
RenderView1.Representations.append(ScalarBarWidgetRepresentation)

Render()

# SET PROPER CAMERA POSITION============================================
ResetCamera()
RenderView1 = GetRenderView()
RenderView1.CameraViewUp = [-0.9, 0.1, 0.4]
RenderView1.CameraPosition = [0.06,0.14,0.09]

Render()

# LOAD THE CASE AGAIN TO DISPLAY THE CHANNEL============================
showWalls = PV4FoamReader(FileName=mainCase[0], guiName='showWalls')
showWalls.MeshParts     = ['wall - group']
showWalls.VolumeFields  = []

showWallsRepresentation                 = Show()
showWallsRepresentation.Representation  = 'Surface'
showWallsRepresentation.Visibility      = 1
showWallsRepresentation.DiffuseColor    = [0.5529411764705883, 0.5529411764705883, 0.5529411764705883]

Render()


# ANIMATION SAVING (PURE IMAGES, NOT BLENDER)===========================
#~ eTime   = float("%s"%AnimationScene1.GetProperty('Duration'))
#~ 
#~ AnimationScene1.GoToFirst()
#~ k       = 0;
#~ cTime   = float("%s"%AnimationScene1.GetProperty('AnimationTime'))
#~ 
#~ while (cTime < eTime):
    #~ Render()
    #~ #x3dExporter=exporters.X3DExporter(FileName='./x3dFiles/rivulet_%03d.x3d'% (k))
    #~ #x3dExporter.SetView(GetActiveView()) # <===== NEW LINE
    #~ #x3dExporter.Write()
    #~ WriteImage('pvAnimation/plate_%03d.png'%k)
    #~ AnimationScene1.GoToNext()
    #~ k = k+1
    #~ cTime   = float("%s"%AnimationScene1.GetProperty('AnimationTime'))

