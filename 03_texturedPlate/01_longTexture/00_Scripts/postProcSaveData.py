#!/usr/bin/python

#FILE DESCRIPTION=======================================================
#~ Python script used for post-processing automatization of flow on an
#~ inclined (?textured?) plate. Calculates and saves aW/aT
#~
#~ NOTES:
    
#~ USAGE:
   #~ paraFoam --script=./postProcSaveData.py 


#LICENSE================================================================
#  prostProcSaveData.py
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
# -- folder for saving the output data
outDataFolder = "/media/martin/Data_2/05_TextPlate/10_noTexture/AA_evPrep/10_postProcOutputs/"
# -- file for saving the scalar outputs
scalDataFile  = "iF_scalDataFile"

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
allIntMeshRepresentation.Visibility = 1
allIntMeshRepresentation.Representation = 'Wireframe'
allIntMeshRepresentation.Opacity = 0.1

# set up black background (seems prettier)
RenderView1 = GetRenderView()
RenderView1.UseTexturedBackground = 0
RenderView1.Background = [0.0, 0.0, 0.0]

Render()

activeSource_OpenFOAM = FindSource( mainCase[0][2::] )

# CREATE A SCALAR CLIP - SHOW ONLY THE RIVULET==========================
liqOnly = Clip( ClipType="Scalar", guiName="liqOnly" )

liqOnly.Scalars = ['POINTS', 'alpha.liquid']
liqOnly.Value = 0.5

liqOnlyRepresentation = Show()

liqOnlyRepresentation.Representation = 'Surface'
Render()

# CREATE A SLICE AT Z=EPS (GET WETTED AREA)=============================
wettedPlate = Slice( SliceType="Plane", guiName="wettedPlate" )

wettedPlate.SliceOffsetValues = [0.0]
wettedPlate.SliceType.Origin = [0.0, 0.0, 1.0e-6]                      #slightly above the plate level
wettedPlate.SliceType.Normal = [0.0, 0.0, 1.0]                          #z normal

wettedPlateRepresentation = Show()
wettedPlateRepresentation.Visibility = 1

Render()

# MOVE TO THE LAST TIME STEP============================================
AnimationScene1 = GetAnimationScene()
AnimationScene1.GoToLast()

Render()

# CALCULATE THE WETTED AREA=============================================
SetActiveSource(wettedPlate)
integrateVars = IntegrateVariables( guiName = "integrateVars")          #create the filter

aW = integrateVars.CellData.GetArray('Area').GetRange()#dig out data
aW = aW[0]                                                              #wetted area, m2

# CALCULATE THE TOTAL WETTABLE AREA=====================================
allData = servermanager.Fetch(activeSource_OpenFOAM)
coordMax= allData.GetBlock(0).GetBlock(0).GetBounds()                   #(xMin,xMax,yMin,yMax,zMin,zMax)
aT      = (coordMax[1]-coordMax[0])*(coordMax[3]-coordMax[2])           #rectangular and non-textured

# -- testing outputs - print out aW/aT
print('wetted area ratio, aW/aT = %5.5f'%(aW/aT))
# SAVE THE DATA=========================================================
# Note: I need to find the right row and write (append) the results to it
caseName  = mainCase[0][2::].split('.OpenFOAM')[0]                      #get the case name
caseIdentification = caseName.split('_')                                #split the case name file by data

solver,Re,plateIncl,liqName = caseIdentification[0:4]

Re = "%5.4e"%float(Re[2::])                                             #convert Reynolds number to right format, ommit Re at the beginning

idStr = [liqName + '\t' + plateIncl + '\t' + Re]                        #line encoding

pVals = [
            "%5.4e"%(aW/aT),                                            #wetted to total area ratio
        ]

# write everything to the file
with open(outDataFolder+solver+'_scalDataFile', 'r') as file:
    # read a list of lines into data
    data = file.readlines()
    
for j in range(len(idStr)):
    for i in range(len(data)):
        fInd = data[i].find(idStr[j])
        if fInd>-1:
            data[i] = data[i] = data[i][:fInd] + idStr[j] + '\t' + pVals[j] + '\n'

with open(outDataFolder+solver+'_scalDataFile', 'w') as file:
    file.writelines( data )

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


# ADD SCALAR BAR WITH VELOCITY MAGNITUDE================================
source = liqOnly

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

# SET PROPER CAMERA POSITION============================================
ResetCamera()
RenderView1 = GetRenderView()
RenderView1.CameraViewUp = [-0.9, 0.1, 0.4]
RenderView1.CameraPosition = [0.4,0.9,0.6]

Render()

# SAVE aW/aT DURING THE WHOLE SIMULATION AND SAVE IMAGES FOR ANIMATION)=
aWaTList= ['time\taWaT\n']                                             #prepare variable
eTime   = AnimationScene1.EndTime

AnimationScene1.GoToFirst()
k       = 0;
cTime   = AnimationScene1.AnimationTime

while (cTime < eTime):
    Render()
    #x3dExporter=exporters.X3DExporter(FileName='./x3dFiles/rivulet_%03d.x3d'% (k))
    #x3dExporter.SetView(GetActiveView()) # <===== NEW LINE
    #x3dExporter.Write()
    # -- save image for animation
    WriteImage('pvAnimation/plate_%03d.png'%k)
    # -- calculate current wetted area
    aW = integrateVars.CellData.GetArray('Area').GetRange()#dig out data
    aW = aW[0]
    aWaTList.append("%5.4f"%cTime + "\t" + "%5.5f\n"%(aW/aT))        #append to the data
    # -- move to the next timestep
    AnimationScene1.GoToNext()
    k = k+1
    cTime   = AnimationScene1.AnimationTime
    
# -- save the results
with open(
            outDataFolder + caseName + '_aWaT',
            'w'
        ) as file:
    file.writelines( aWaTList )

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

