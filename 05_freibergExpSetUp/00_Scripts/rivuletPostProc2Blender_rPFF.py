#!/usr/bin/python

#FILE DESCRIPTION=======================================================
#~ Python script used for post-processing automatization of the rivulet
#~ flow down the experimental plate in Freiberg
#~
#~ NOTES:
    #~ - creates a scalar clip for deltaf >= 1e-5
    #~ - rotates everything to y+ position
    #~ - saves the clip colored by U (magnitude)
    #~ - saves the mesh colored by solid color
    #~ - it is kind of minimal script (no descriptions at all)
    #~ - I should polish it quite a bit, but it does what it should
    
    
#~ USAGE:
   #~ paraFoam -region wallFilmRegion --script=./rivuletPostProc2Blender_rPFF.py 


#LICENSE================================================================
#  rivuletProstProc2Blender_rPFF.py
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

mainCase = glob.glob('./*.OpenFOAM')                                     #works only for the cases with 1 foam file

paraview.simple._DisableFirstRenderCameraReset()

activeSource_OpenFOAM = GetActiveSource()

# enable all available fields
activeSource_OpenFOAM.VolumeFields = ['Tf', 'deltaf', 'Uf']

# show all for internal mesh
#~ activeSource_OpenFOAM.MeshParts = ['internalMesh']
# NOTE: I am interested in the wallFilmFaces region
activeSource_OpenFOAM.MeshParts = ['region0_to_wallFilmRegion_wallFilmFaces - patch']

# MAIN MESH PREPARATION=================================================
# I will need to save the main mesh as a surface (blender reasons)
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
liqOnly = Clip( ClipType="Scalar", guiName="liqOnly" )

liqOnly.Scalars = ['POINTS', 'deltaf']
liqOnly.Value = 1e-5

liqOnlyRepresentation = Show()

liqOnlyRepresentation.Opacity = 1.0

source = GetActiveSource()

#~ data = source.GetCellDataInformation()
data = source.GetPointDataInformation()

#get the array and the respective min-max
array = data.GetArray('Uf')
dataRange = array.GetRange(-1)                                          #-1 for magnitude

#INTERMEZZO=============================================================
# -- write the dataRange to blenderPrep.py
idStr = 'velMax      = '

# write everything to the file
with open('blenderPrep_rPFF.py', 'r') as file:
    # read a list of lines into data
    data = file.readlines()
    
for i in range(len(data)):
    fInd = data[i].find(idStr)
    if fInd>-1:
        data[i] = (data[i][:fInd] + idStr + "%5.3e"%dataRange[1] + '\n')

with open('blenderPrep_rPFF.py', 'w') as file:
    file.writelines( data )
#=======================================================================

# PROPER COLORING=======================================================

a3_U_PVLookupTable = GetLookupTableForArray( "Uf", 3,
    RGBPoints=[0.0, 0.0, 0.0, 1.0, dataRange[1], 1.0, 0.0, 0.0],
    VectorMode='Magnitude',
    ScalarRangeInitialized=1.0 )

a3_U_PiecewiseFunction = CreatePiecewiseFunction( Points=[0.0, 0.0, 0.5, 0.0, 1.0, 1.0, 0.5, 0.0] )

liqOnlyRepresentation.Representation = 'Surface'
liqOnlyRepresentation.ColorArrayName = ('POINT_DATA', 'Uf')
liqOnlyRepresentation.LookupTable = a3_U_PVLookupTable

a3_U_PVLookupTable.ScalarOpacityFunction = a3_U_PiecewiseFunction
        
Render()

# I do not want to see the original results
allIntMeshRepresentation.Visibility = 0

Render()

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



