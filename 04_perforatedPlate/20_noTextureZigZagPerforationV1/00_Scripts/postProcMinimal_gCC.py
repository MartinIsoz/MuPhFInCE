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
import math

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

activeSource_OpenFOAM = FindSource( mainCase[0][2::] )

# CREATE A SCALAR CLIP - SHOW ONLY THE RIVULET==========================
liqOnly = Clip( ClipType="Scalar", guiName="liqOnly" )

liqOnly.Scalars = ['POINTS', 'alpha.liquid']
liqOnly.Value = 0.5

liqOnlyRepresentation = Show()

liqOnlyRepresentation.Representation = 'Surface'
liqOnlyRepresentation.Visibility = 1
liqOnlyRepresentation.Opacity    = 0.5

# CREATE A SCALAR CLIP - SHOW ONLY THE GAS PHASE========================
SetActiveSource(activeSource_OpenFOAM)

gasOnly = Clip( ClipType="Scalar", guiName="gasOnly" )

gasOnly.Scalars = ['POINTS', 'alpha.liquid']
gasOnly.Value = 0.05
gasOnly.InsideOut = 1

gasOnlyRepresentation = Show()

gasOnlyRepresentation.Representation = 'Surface'
gasOnlyRepresentation.Visibility = 0

# COLOR THE FILM BY FILM THICKNESS (CALCULATOR+PROPER COLORING)=========
SetActiveSource(liqOnly)                                                #reset the active source
fThCalc  = Calculator( guiName="fThCalc" )

fThCalc.Function = 'coordsZ'
fThCalc.ResultArrayName = 'hFun'

fThCalcRepresentation = Show()
fThCalcRepresentation.Visibility = 0

# GET THE COMP DOMAIN DIMENSIONS========================================
allData = servermanager.Fetch(activeSource_OpenFOAM)
coordMax= allData.GetBlock(0).GetBlock(0).GetBounds()                   #(xMin,xMax,yMin,yMax,zMin,zMax)
domSize = [                                                             #computational domain size
             coordMax[1]-coordMax[0],
             coordMax[3]-coordMax[2],
             coordMax[5]-coordMax[4],
          ]
# -- find the domain middle
domMid  = [ (coordMax[1]-coordMax[0])/2,                                #domain middle
            (coordMax[3]-coordMax[2])/2,
            (coordMax[5]-coordMax[4])/2,
          ]

# CREATE GAS FLOW STREAMLINES===========================================
SetActiveSource(gasOnly)
gasUStrLines = StreamTracer( guiName="gasUStrLines" )

#~ gasUStrLines.SeedType = "High Resolution Line Source"                   #line oriented by the z axis
#~ gasUStrLines.SeedType.Point1 = [
                                #~ domSize[0]/2,
                                #~ domSize[1]/2,
                                #~ coordMax[4],
                               #~ ]
#~ gasUStrLines.SeedType.Point2 = [
                                #~ domSize[0]/2,
                                #~ domSize[1]/2,
                                #~ coordMax[5],
                               #~ ]
#~ gasUStrLines.SeedType.Resolution       = 200

gasUStrLines.SeedType = "Point Source"
gasUStrLines.SeedType.Center = domMid
gasUStrLines.SeedType.Radius = domSize[1]/2                             #I want to cover all the the cell
gasUStrLines.SeedType.NumberOfPoints = 1000

gasUStrLines.MaximumStreamlineLength = math.sqrt(domSize[0]**2+domSize[1]**2+domSize[2]**2)

gasUStrLinesRepresentation = Show()
gasUStrLinesRepresentation.Visibility = 1


# CREATE SLICE AT THE DOMAIN MIDDLE=====================================
SetActiveSource(activeSource_OpenFOAM)                                  #reset the active source
# -- create the slice
yNormSlice = Slice( SliceType="Plane", guiName="yNormSlice" )

yNormSlice.SliceOffsetValues = [0.0]
yNormSlice.SliceType.Origin = domMid                                    #set the origin to domain middle
yNormSlice.SliceType.Normal = [0.0, 1.0, 0.0]                           #y normal

yNormSliceRepresentation = Show()
yNormSliceRepresentation.Visibility = 0

Render()

# CREATE LIQUID ONLY AND GAS ONLY CLIPS=================================
liqOnlySl = Clip( ClipType="Scalar", guiName="liqOnlySl" )

liqOnlySl.Scalars = ['POINTS', 'alpha.liquid']
liqOnlySl.Value = 0.5

liqOnlySlRepresentation = Show()

liqOnlySlRepresentation.Representation = 'Surface'
liqOnlySlRepresentation.DiffuseColor   = [0.0,0.0,1.0]
liqOnlySlRepresentation.Visibility = 1

SetActiveSource(yNormSlice)                                             #reset the active source

gasOnlySl = Clip( ClipType="Scalar", guiName="gasOnlySl" )

gasOnlySl.Scalars   = ['POINTS', 'alpha.liquid']
gasOnlySl.Value     = 0.05
gasOnlySl.InsideOut = 1

gasOnlySlRepresentation = Show()

gasOnlySlRepresentation.Representation = 'Surface'
gasOnlySlRepresentation.Visibility = 0

# CREATE INTERFACE REGIONS==============================================
SetActiveSource(liqOnlySl)

liqIntR = Clip( ClipType="Scalar", guiName="liqIntR" )

liqIntR.Scalars = ['POINTS', 'alpha.liquid']
liqIntR.Value   = 0.55
liqIntR.InsideOut=1

liqIntRRepresentation = Show()
liqIntRRepresentation.Representation = 'Surface'
liqIntRRepresentation.DiffuseColor   = [1.0,0.0,0.0]
liqIntRRepresentation.Visibility = 1

# CREATE GLYPHS (VELOCITY VECTOR FIELDS)================================
SetActiveSource(liqIntR)                                                #reset the active source
# -- creation of the vector field itslef
liqIntVelF = Glyph( guiName="liqIntVelF" )

# -- basic settings
liqIntVelF.GlyphTransform = "Transform2"
liqIntVelF.GlyphType      = "Arrow"
liqIntVelF.Scalars  = ['POINTS', 'alpha.liquid']
liqIntVelF.Vectors  = ['POINTS', 'U']
liqIntVelF.ScaleMode= 'vector'
liqIntVelF.SetScaleFactor = 1e-2                                        #extremely ugly, but I need to shrink velocities of order of magnitude approx 0.1 m/s to mm/s (cell is 60 x 50 x 7 mm)
# -- modify the display properties
liqIntVelF.MaximumNumberofPoints = 200
liqIntVelF.GlyphType.TipRadius      = 0.04
liqIntVelF.GlyphType.ShaftRadius    = 0.02

liqIntVelFRepresentation = Show()
liqIntVelFRepresentation.DiffuseColor = [1.0,0.0,0.0]

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


# ADD SCALAR BAR WITH VELOCITY MAGNITUDE================================
#~ source = gasOnlySl
#~ colorObjectRepresentation = gasOnlySlRepresentation                     #what object will be colored
source = gasUStrLines
colorObjectRepresentation = gasUStrLinesRepresentation                     #what object will be colored

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

colorObjectRepresentation.Representation = 'Surface'
colorObjectRepresentation.ColorArrayName = ('POINT_DATA', 'U')
colorObjectRepresentation.LookupTable = a3_U_PVLookupTable

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

# SCALAR BAR============================================================
#~ source = fThCalc                                                        #where to get the data
#~ 
#~ data = source.GetPointDataInformation()
#~ 
#~ #get the array and the respective min-max
#~ array = data.GetArray('hFun')
#~ dataRange = array.GetRange(0)                                          #-1 for magnitude
#~ 
#~ colorObjectRepresentation = fThCalcRepresentation                       #what object will be colored
#~ 
#~ a0_hFun_PVLookupTable = GetLookupTableForArray( "hFun", 0,
    #~ RGBPoints=[0.0, 0.0, 0.0, 0.0, dataRange[1], 1.0, 1.0, 1.0],     #grayscale coloring
    #~ ColorSpace='RGB',
    #~ RGBPoints=[0.0, 0.0, 0.0, 1.0, dataRange[1], 1.0, 0.0, 0.0],        #classical rainbow coloring
    #~ ColorSpace='HSV',
    #~ ScalarRangeInitialized=1.0 )
#~ 
#~ a0_hFun_PiecewiseFunction = CreatePiecewiseFunction( Points=[0.0, 0.0, 0.5, 0.0, 1.0, 1.0, 0.5, 0.0] )
#~ 
#~ colorObjectRepresentation.Representation = 'Surface'
#~ colorObjectRepresentation.ColorArrayName = ('POINT_DATA', 'hFun')
#~ colorObjectRepresentation.LookupTable = a0_hFun_PVLookupTable
#~ 
#~ a0_hFun_PVLookupTable.ScalarOpacityFunction = a0_hFun_PiecewiseFunction
        #~ 
#~ Render()
#~ 
#~ ScalarBarWidgetRepresentation = CreateScalarBar( Title='$h(x,y),[\mathrm{m}]$',
 #~ ComponentTitle='',
 #~ LabelFontSize=12,
 #~ Enabled=1,
 #~ LookupTable=a0_hFun_PVLookupTable,
 #~ TitleFontSize=14,
 #~ LabelFormat='$%-#5.2e$')
#~ RenderView1.Representations.append(ScalarBarWidgetRepresentation)
#~ 
#~ Render()

# SET PROPER CAMERA POSITION============================================
ResetCamera()
RenderView1 = GetRenderView()
RenderView1.CameraViewUp = [-0.9, 0.1, 0.4]
RenderView1.CameraPosition = [0.4,0.9,0.6]

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

