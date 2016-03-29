#!/usr/bin/python

#FILE DESCRIPTION=======================================================
#~ Python script used for post-processing automatization of the rivulet
#~ flow down the experimental plate in Freiberg
#~ 
#~ The script creates set of exportable planes for BLENDER (x3d files)
#~
#~ NOTES:
    #~ - creates a scalar clip for alpha >= 0.5
    #~ - rotates everything to y+ position
    #~ - saves the clip colored by U (magnitude)
    #~ - saves the mesh colored by solid color
    #~ - it is kind of minimal script (no descriptions at all)
    #~ - I should polish it quite a bit, but it does what it should
    
#~ USAGE:
   #~ paraFoam --script=./rivuletPostProc2Blender.py 


#LICENSE================================================================
#  rivuletProstProc2Blender.py
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
try: paraview
except: from paraview import *
try: paraview.simple
except: from paraview.simple import *
conn = servermanager.ActiveConnection
misc = conn.Modules.misc
exporters = servermanager.createModule("exporters", misc)
import math
import glob
import string

mainCase = glob.glob('./*.OpenFOAM')                                    #works only for the cases with 1 foam file

paraview.simple._DisableFirstRenderCameraReset()

activeSource_OpenFOAM = GetActiveSource()

# enable all available fields
activeSource_OpenFOAM.VolumeFields = ['alpha.liquid', 'p_rgh', 'U']

# show all for internal mesh
activeSource_OpenFOAM.MeshParts = ['internalMesh']

# I dont want to see the main mesh / I do want to see it as transparent wireframe
allIntMeshRepresentation = GetDisplayProperties( activeSource_OpenFOAM )


# set up black background (seems prettier)
RenderView1 = GetRenderView()
RenderView1.UseTexturedBackground = 0
RenderView1.Background = [0.0, 0.0, 0.0]

Render()

# rotate the scene to y+ position
RenderView1 = GetRenderView()
RenderView1.CameraViewUp = [0.0, 0.0, 1.0]
RenderView1.CameraPosition = [0.145, -0.62, -0.0035]
RenderView1.CameraFocalPoint = [0.145, 0.0, -0.0035]
RenderView1.CameraClippingRange = [0.5, 0.7]

Render()

x3dExporter=exporters.X3DExporter(FileName="./x3dFiles/internalMesh.x3d")
x3dExporter.SetView(GetActiveView()) # <===== NEW LINE
x3dExporter.Write()

activeSource_OpenFOAM = FindSource( mainCase[0] )

# GO TO THE ANIMATION (TIME RANGE) END==================================
AnimationScene1 = GetAnimationScene()
AnimationScene1.GoToLast()
Render()

# CREATE A SCALAR CLIP - SHOW ONLY THE RIVULET==========================
liqOnly = Clip( ClipType="Scalar" ) 

liqOnly.Scalars = ['POINTS', 'alpha.liquid']

liqOnly.Value = 0.5

liqOnlyRepresentation = Show()


liqOnlyRepresentation.Opacity = 1.0

source = GetActiveSource()

#~ data = source.GetCellDataInformation()
data = source.GetPointDataInformation()

#get the array and the respective min-max
array = data.GetArray('U')
dataRange = array.GetRange(-1)                                          #-1 for magnitude

#INTERMEZZO=============================================================
# -- write the dataRange to blenderPrep.py
idStr = 'velMax      = '

# write everything to the file
with open('blenderPrepV2.py', 'r') as file:
    # read a list of lines into data
    data = file.readlines()
    
for i in range(len(data)):
    fInd = data[i].find(idStr)
    if fInd>-1:
        data[i] = (data[i][:fInd] + idStr + "%5.3e"%dataRange[1] + '\n')

with open('blenderPrepV2.py', 'w') as file:
    file.writelines( data )
#=======================================================================

#~ liqOnlyRepresentation.Representation = 'Surface'
#~ liqOnlyRepresentation.ColorArrayName = ('POINT_DATA', 'U')

a3_U_PVLookupTable = GetLookupTableForArray( "U", 3,
    RGBPoints=[0.0, 0.0, 0.0, 1.0, dataRange[1], 1.0, 0.0, 0.0],
    VectorMode='Magnitude',
    ScalarRangeInitialized=1.0 )

a3_U_PiecewiseFunction = CreatePiecewiseFunction( Points=[0.0, 0.0, 0.5, 0.0, 1.0, 1.0, 0.5, 0.0] )

#~ a3_U_PVLookupTable = GetLookupTableForArray( "U", 4,
    #~ RGBPoints=[dataRange[0], 0.0, 0.0, 1.0, dataRange[1], 1.0, 0.0, 0.0],
    #~ VectorMode='Magnitude',
    #~ ScalarRangeInitialized=1.0 )
    

liqOnlyRepresentation.Representation = 'Surface'
liqOnlyRepresentation.ColorArrayName = ('POINT_DATA', 'U')
liqOnlyRepresentation.LookupTable = a3_U_PVLookupTable

a3_U_PVLookupTable.ScalarOpacityFunction = a3_U_PiecewiseFunction
        
Render()

# PREPARE SCALAR CLIP FOR SAVING========================================

# camera position

#~ ResetCamera()
#~ RenderView1 = GetRenderView()
#~ RenderView1.CameraViewUp = [-0.8, -0.5, 0]
#~ RenderView1.CameraFocalPoint = [0.15,-0.1,0]                               #center of the plate
#~ RenderView1.CameraClippingRange = [5, 5]                                #who knows what it does...
#~ RenderView1.CameraPosition = [0.2,0.15,0.2]
#~ 
#~ Render()

# I do not want to see the original results
allIntMeshRepresentation.Visibility = 0

Render()

#~ x3dExporter=exporters.X3DExporter(FileName="./x3dFiles/rivulet.x3d")
#~ x3dExporter.SetView(GetActiveView()) # <===== NEW LINE
#~ x3dExporter.Write()
#~ 
# ANIMATION PREPARATION=================================================
eTime   = float("%s"%AnimationScene1.GetProperty('Duration'))

AnimationScene1.GoToFirst()
k       = 0;
cTime   = float("%s"%AnimationScene1.GetProperty('AnimationTime'))

while (cTime < eTime):
    Render()
    x3dExporter=exporters.X3DExporter(FileName='./x3dFiles/rivulet_%03d.x3d'% (k))
    x3dExporter.SetView(GetActiveView()) # <===== NEW LINE
    x3dExporter.Write()
    AnimationScene1.GoToNext()
    k = k+1
    cTime   = float("%s"%AnimationScene1.GetProperty('AnimationTime'))


