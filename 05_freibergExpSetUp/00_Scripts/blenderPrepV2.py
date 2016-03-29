#!/usr/bin/python

#FILE DESCRIPTION=======================================================
#~ Python script used for post-processing automatization of the rivulet
#~ flow down the experimental plate in Freiberg
#~ 
#~ The script loads data exported from paraview and further prepares
#~ them for blender postprocessing
#~
#~ NOTES:
    #~ - loads data
    #~ - scales and rotates data
    #~ - loads the experimental cell model
    #~ - puts everything together
    #~ - prepares materials for the rendering
    
#~ USAGE:
   #~ blender --python blenderPrepV1.py


#LICENSE================================================================
#  blenderPrep.py
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
import bpy
import math

#CUSTOM FUNCTIONS AND DICTIONARIES======================================

#CONSTANTS==============================================================
plateIncl   = 7.85398e-01
mDot        = 3.02075e+00
liqName     = "H2O"
scaleData   = 3.925                                                     #how to scale data (fit with exp. cell)

dataLoc     = [-0.37278,-0.01351,1.61874]                                       #get proper data location

blendPath   = "/media/martin/Data_3/05_PlateDCases/02_CADS/Geometry_Blender/geomV5.blend"
flName      = [["Plane","Lamp","Lamp.001","Lamp.002","MainCamera"],["ExpCell"]]
geomDir     = [blendPath + "/Object/",blendPath + "/Group/"]

dataDir     = "x3dFiles/"
strTime     =  0.00
endTime     = 10.0
tStep       = 0.0400
nFrames     = int((endTime-strTime)/tStep-1)                            #number of frames (starts with 0)

# -- resolution
resW        = 1920
resH        = 1200
resPerc     = 100
imDir       = "blenderOUT/"

# -- case description
velMax      = 1.365e+00
velMin      = 0                                                         #velocity minimum [m/s]
nCSteps     = 5                                                         #steps between min and max
cStep       = (velMax-velMin)/nCSteps                                   #step magnitude
    
#DELETE ALL THE UNUSED OBJECTS==========================================
for ob in bpy.context.scene.objects:
    ob.select = ob.type == 'LAMP' or ob.type == 'MESH' or ob.type == 'CAMERA'
bpy.ops.object.delete()

#IMPORT PREPARED GEOMETRY
for i in range(len(geomDir)):
    for nms in flName[i]:
        flPath  = geomDir[i] + nms
        bpy.ops.wm.link_append(filepath=flPath, filename=nms, directory=geomDir[i],link=0)

#IMPORT THE DATA========================================================
bpy.ops.import_scene.x3d(filepath=dataDir + "internalMesh.x3d")         #import mesh
#~ bpy.ops.import_scene.x3d(filepath=dataDir + "rivulet.x3d")
for k in range(nFrames):
    bpy.ops.import_scene.x3d(filepath=dataDir +'rivulet_%03d.x3d'% (k))

# -- Note:
#~ -   mesh is always ShapeIndexedFaceSet and all the rivulet snapshots
    #~ are ShapeIndexedFaceSet.DDD
#~ -   e.g. mats can be accessed by Shape.DDD for rivulet and Shape for 
    #~ mesh

#DELETE ALL THE TODO OBJECTS============================================
for ob in bpy.context.scene.objects:
    ob.select = ob.type == 'LAMP' and ob.name.startswith("TODO")
bpy.ops.object.delete()

#DELETE ALL THE VIEWPOINTS==============================================
for ob in bpy.context.scene.objects:
    ob.select = ob.type == 'CAMERA' and ob.name.startswith("Viewpoint")
bpy.ops.object.delete()

#SELECT AND MODIFY ALL THE SHAPEINDEXEDFACESET==========================
for ob in bpy.context.scene.objects:
    if ob.type == 'MESH' and ob.name.startswith("ShapeIndexedFaceSet"):
        # -- rotate imported
        ob.rotation_euler[0] = 0
        ob.rotation_euler[1] = math.pi/3                                #this is the default plate angle
        ob.rotation_euler[2] = 0
        # -- scale imported
        ob.scale[0] = scaleData
        ob.scale[1] = scaleData
        ob.scale[2] = scaleData
        # -- move imported to the right place
        for i in range(len(dataLoc)):
            ob.location[i] = dataLoc[i]
            
#ADJUST THE INCLINATION OF EXPERIMENTAL CELL============================    
# MAIN IDEA:
    #~ - set plate as a parent of all the objects (cell + data)
    #~ - incline all by inclining the parent (plate)
    
bpy.ops.object.select_all(action='DESELECT')                            #deselect all the objects

for ob in bpy.context.scene.objects:                                    #select all the imported data
    if ob.type == 'MESH' and ob.name.startswith("ShapeIndexedFaceSet"):
        ob.select = True
for obj in ["plate","CovGlass","TopCover"]:                             #select the experimental cell
    bpy.data.objects[obj].select = True
    
bpy.context.scene.objects.active = bpy.data.objects["plate"]            #make the plate active

bpy.ops.object.parent_set()                                             #will set plate as parent

bpy.data.objects["plate"].rotation_euler[1]=plateIncl                   #should rotate all
    
            
#PREPARE EVERYTHING FOR RENDER==========================================
# -- world (horizon and all)
bpy.data.worlds["World"].horizon_color = [0,0,0]
# -- mesh
bpy.data.materials["Shape"].type="WIRE"                                 #type of material
bpy.data.materials["Shape"].emit=0.1                                    #amount of light to emit
bpy.data.materials["Shape"].ambient=0.1                                 #amount of global amb. col.
bpy.data.materials["Shape"].use_transparency=1
bpy.data.materials["Shape"].alpha=1.0

# -- rivulet
#~ bpy.data.materials["Shape.001"].type="WIRE"                          #type of material
for k in range(nFrames):
    bpy.data.materials["Shape.%03d"% (k+1)].emit=0.7                    #amount of light to emit
    bpy.data.materials["Shape.%03d"% (k+1)].ambient=0.6                 #amount of global amb. col.
    bpy.data.objects["ShapeIndexedFaceSet.%03d"% (k+1)].hide_render=1   #hide current version for render
#~ bpy.data.materials["Shape.001"].use_transparency=1
#~ bpy.data.materials["Shape.001"].alpha=0.1

# --scene
bpy.context.scene.camera = bpy.context.scene.objects["MainCamera"]          #activate the imported camera

# --case description
caseName    = liqName + " on wetted steel"
inclName    = "plate inclination = " + "%2.0f"%(plateIncl/math.pi*180) + "°"
flRtName    = "flow rate = " + "%5.2f"%mDot + " g/s"
bpy.ops.object.text_add()
caseDesc    = bpy.context.object
caseDesc.data.body = (caseName + "\n\n" + 
                                inclName + "\n\n" + 
                                flRtName + "\n\n\n\n\n\n\n\n\n\n" + 
                               "geometry based on experimental set-up from\n" +
                               "TU Bergkademie Freiberg\n" + 
                               "(authored by Andre Marek)")
caseDesc.rotation_euler[2]=math.pi/2
caseDesc.scale[0]         =0.2
caseDesc.scale[1]         =0.2
caseDesc.scale[2]         =0.2        
caseDesc.location[0]      =-1.4                       
caseDesc.location[1]      =-1.9                       
caseDesc.location[2]      =0.06     

textMat = bpy.data.materials.new(name="MaterialText")                   #create material for texts
caseDesc.data.materials.append(textMat)
textMat.diffuse_color=[0.2,0.2,0.2]
textMat.emit = 0.2
textMat.use_transparency = 1

# --add time notation
bpy.ops.object.text_add()
timeDesc    = bpy.context.object
timeDesc.data.body = "t = %5.2f s"% (0*tStep)
timeDesc.rotation_euler[2]=math.pi/2
timeDesc.scale[0]         =0.2
timeDesc.scale[1]         =0.2
timeDesc.scale[2]         =0.2        
timeDesc.location[0]      =1.8                       
timeDesc.location[1]      =0.95                       
timeDesc.location[2]      =0.06
timeDesc.data.materials.append(textMat)

# --add colorbar
bpy.ops.mesh.primitive_plane_add()                                      #add plane
colorBar    = bpy.context.object
colorBar.scale[0]         =1                                            #move and scale it
colorBar.scale[1]         =0.05
colorBar.scale[2]         =1       
colorBar.location[0]      =-0.15                       
colorBar.location[1]      =1.5                      
colorBar.location[2]      =0.06
colorBar.name             ="colorBar"

cBarMat = bpy.data.materials.new(name="MaterialCBar")                   #create material for colorbar
colorBar.data.materials.append(cBarMat)                                 #appand material to colorbar
bpy.data.materials["MaterialCBar"].emit = 0.3

cBarTex = bpy.data.textures.new(name="TextureCBar",type = "BLEND")      #create a texture
cBarTex.use_color_ramp = 1                                              #use color ramp (transition)
cBarTex.color_ramp.interpolation = "CARDINAL"                           #set color ramp interpolation

cBarTex.color_ramp.elements[0].position = 0.0                           #red ramp stop
cBarTex.color_ramp.elements[0].color = [1.0,0.0,0.0,1.0]                #rgba
cBarTex.color_ramp.elements[1].position = 0.5                           #green ramp stop
cBarTex.color_ramp.elements[1].color = [0.0,1.0,0.0,1.0]                #rgba
cBarTex.color_ramp.elements.new(position=1.0)                           #blue ramp stop
cBarTex.color_ramp.elements[2].color = [0.0,0.0,1.0,1.0]                #rgba

cBarMatTSlot = cBarMat.texture_slots.add()                              #create slot for texture
cBarMatTSlot.texture = cBarTex                                          #add texture to it

# --add colorbar description
bpy.ops.object.text_add()
cBarName    = bpy.context.object
cBarName.data.body = "norm(u), [m/s]"
#~ cBarName.rotation_euler[2]=math.pi/2
cBarName.scale[0]         =0.2
cBarName.scale[1]         =0.2
cBarName.scale[2]         =0.2        
cBarName.location[0]      =-0.75                       
cBarName.location[1]      =1.7                       
cBarName.location[2]      =0.06
cBarName.data.materials.append(textMat)

posXMin     = -1.0
posXMax     = 0.8
xStep       = (posXMax-posXMin)/nCSteps
cValName    = []
for i in range(nCSteps+1):
    bpy.ops.object.text_add()
    cValName.append(bpy.context.object)
    cValName[i].data.body = "%5.1f"% (i*cStep)
    cValName[i].scale[0]         =0.2
    cValName[i].scale[1]         =0.2
    cValName[i].scale[2]         =0.2
    cValName[i].rotation_euler[2]=math.pi/2
    cValName[i].location[0]      =posXMax-i*xStep                       
    cValName[i].location[1]      =1.05                       
    cValName[i].location[2]      =0.06
    cValName[i].data.materials.append(textMat)
    




#RENDER ANIMATION=======================================================
# NOTE: only the simplest case - flowing rivulet
#       - this way, I can render each image separately and then combine
#         it with AVCONV
# NOTE: 24 fps

# ONCE, I WOULD PROBABLY NEED TO BASE TO SOLUTION ON THIS
# For instance you first define T_START, T_END and LAST_FRAME  
# T_START and T_END as the first and last frames that the object will be visible in.  
# Having an additional keyframe on either side of those frames allows you to play  
# the sequence backwards without messing up the hide duration.    
# "hide" ( hides from view ) use "hide_render" to make it apply to render.  
    #~ time_and_state_settings = ( (0,False),   
                                #~ (T_START-1, False),  
                                #~ (T_START, True),  
                                #~ (T_END, True),  
                                #~ (T_END+1, False),  
                                #~ (LAST_FRAME, False))
#~ NOTE: SCRIPT
    #~ - do nothing
    #~ - rotate mesh around z axis
    #~ - zoom out 
    #~ - disappear mesh and appear experimental cell
    #~ - start animation

fps        = 24

dNthFrames = 2*fps                                                      #nothing is done during this time

rotMeshFrames = 4*fps                                                   #number of frames for mesh rotation
rotZInit      = 0.0*math.pi
rotZFinal     = 2.0*math.pi
rotZStep      = (rotZFinal-rotZInit)/rotMeshFrames
                                
zoomOutFrames   = 4*fps                                                 #number of frames for zoom out
camLocInit      = [5.64952,-2.62863,4.77298]                            #camera initial location
camRotInit      = [1.10871,0.01327,1.14827]                             #camera initial rotation
camSizInit      = 5                                                     #camera initial size
camLocFinal     = [6.21846,-2.84367,3.5534]                             #camera final location
camRotFinal     = [1.10871,0.01327,1.14827]                             #camera final rotation
camSizFinal     = 32                                                    #camera final size

camLocStep      = [0,0,0]
camLocCurr      = [0,0,0]
for i in range(len(camLocStep)):                                        #linear change of location
    camLocStep[i] = (camLocFinal[i]-camLocInit[i])/zoomOutFrames
        
camSizStep      = (camSizFinal-camSizInit)/zoomOutFrames

disappFrames    = 4*fps                                                 #number of frames for cell appearance
meshAlphaInit   = 1.0
seeThroughCoef  = 100                                                   #alphaPlastic = alpha/seeTCoeff
meshAlphaFinal  = 0.0
meshAlphaStep   = (meshAlphaFinal-meshAlphaInit)/disappFrames
cellSpIntInit   = 0.0                                                   #cell specular intensity (initial)
cellSpIntFinal  = 0.5                                                   #cell specular intensity (final)
cellSpIntStep   = (cellSpIntFinal-cellSpIntInit)/disappFrames

# -- in case of pure animation (no mesh presentation)
#~ dNthFrames    = 0
#~ rotMeshFrames = 0
#~ zoomOutFrames = 0
#~ disappFrames  = 0
skipFrames    = 0

#~ bpy.data.objects["MainCamera"].rotation_euler = camRotInit
#~ 
#~ # -- make all the materials besides the mesh see through
#~ for ob in bpy.data.materials:                                           #make sure all my materials use transparency
    #~ ob.use_transparency = 1
    # #~ if not ob.name.startswith("MatBrushedSteel"):                       #not at all pretty
    #~ if not ob.name.startswith("Shape"):
        #~ ob.alpha = 0
        #~ ob.specular_intensity = 0                                       #default = 0.5
#~ # -- hide all the objects besides the mesh for rendering
#~ for ob in bpy.data.objects:
    #~ if (not ob.name.startswith("Shape")) and (ob.type=='MESH'):
        #~ ob.hide_render=1                                                #and hide them for rendering
    #~ 
#~ 
#~ # -- nothing is done during this part of animation
#~ bpy.data.objects["MainCamera"].location = camLocInit
#~ bpy.data.cameras["MainCamera"].sensor_width = camSizInit
#~ bpy.context.scene.objects.active = bpy.context.scene.objects.active
#~ for k in range(dNthFrames+1):
    #~ bpy.data.scenes["Scene"].render.filepath = imDir+"animation_%03d.png"% (k)
    #~ bpy.data.scenes["Scene"].render.resolution_x = resW #perhaps set resolution in code
    #~ bpy.data.scenes["Scene"].render.resolution_y = resH
    #~ bpy.data.scenes["Scene"].render.resolution_percentage = resPerc
    #~ bpy.ops.render.render( write_still=True )
    #~ 
#~ # -- mesh is rotated around z axis
#~ for k in range(rotMeshFrames+1):
    #~ bpy.data.objects["ShapeIndexedFaceSet"].rotation_euler[2] = rotZInit+k*rotZStep
    #~ bpy.context.scene.objects.active = bpy.context.scene.objects.active
    #~ bpy.data.scenes["Scene"].render.filepath = imDir+"animation_%03d.png"% (k+dNthFrames)
    #~ bpy.data.scenes["Scene"].render.resolution_x = resW #perhaps set resolution in code
    #~ bpy.data.scenes["Scene"].render.resolution_y = resH
    #~ bpy.data.scenes["Scene"].render.resolution_percentage = resPerc
    #~ bpy.ops.render.render( write_still=True )   
    #~ 
#~ bpy.data.objects["ShapeIndexedFaceSet"].rotation_euler[2] = rotZFinal
#~ 
    #~ 
#~ # -- camera zooms out to see the whole scene
#~ for k in range(zoomOutFrames+1):                               
    #~ for i in range(len(camLocStep)):
        #~ camLocCurr[i] = camLocInit[i] + k*camLocStep[i]
    #~ bpy.data.objects["MainCamera"].location = camLocCurr
    #~ bpy.data.cameras["MainCamera"].sensor_width = camSizInit + k*camSizStep
    #~ bpy.context.scene.objects.active = bpy.context.scene.objects.active
    #~ bpy.data.scenes["Scene"].render.filepath = imDir+"animation_%03d.png"% (k+dNthFrames+rotMeshFrames)
    #~ bpy.data.scenes["Scene"].render.resolution_x = resW #perhaps set resolution in code
    #~ bpy.data.scenes["Scene"].render.resolution_y = resH
    #~ bpy.data.scenes["Scene"].render.resolution_percentage = resPerc
    #~ bpy.ops.render.render( write_still=True )
    #~ 
    #~ 
#~ # -- reappear all the objects besides the mesh for rendering
#~ for ob in bpy.data.objects:
    #~ if (not ob.name.startswith("Shape")) and (ob.type=='MESH'):
        #~ ob.hide_render=0
        #~ 
#~ # -- mesh slowly disappears and the cell appears
#~ for k in range(disappFrames+1):                               
    #~ bpy.data.materials["Shape"].alpha=meshAlphaInit + k*meshAlphaStep
    #~ bpy.data.materials["Shape"].specular_intensity=cellSpIntFinal - k*cellSpIntStep
    #~ for ob in bpy.data.materials:                                       #adjust visibility and everything for all the materials except internal mesh
        ###~ if not ob.name.startswith("MatBrushedSteel"):
        #~ if not ob.name.startswith("Shape"):
            #~ ob.alpha = meshAlphaFinal - k*meshAlphaStep
            #~ if ob.name.startswith("MatClearPlastic"):                    #cell cover plastic has lower alpha
                #~ ob.alpha = ob.alpha/seeThroughCoef
            #~ ob.specular_intensity = cellSpIntInit + k*cellSpIntStep
    #~ bpy.context.scene.objects.active = bpy.context.scene.objects.active
    #~ bpy.data.scenes["Scene"].render.filepath = imDir+"animation_%03d.png"% (k+zoomOutFrames+dNthFrames+rotMeshFrames)
    #~ bpy.data.scenes["Scene"].render.resolution_x = resW #perhaps set resolution in code
    #~ bpy.data.scenes["Scene"].render.resolution_y = resH
    #~ bpy.data.scenes["Scene"].render.resolution_percentage = resPerc
    #~ bpy.ops.render.render( write_still=True )
    #~ 
#~ bpy.data.objects["ShapeIndexedFaceSet"].hide_render=1                   #hide the mesh completely
    #~ 
    #~ 
#~ # -- lets start with the animation (liquid flow)
#~ for k in range(nFrames):
    #~ timeDesc.data.body = "t = %5.2f s"% (k*tStep)
    #~ bpy.data.objects["ShapeIndexedFaceSet.%03d"% (k+1)].hide_render=0    #unhide current version for render
    #~ bpy.data.scenes["Scene"].render.filepath = imDir+"animation_%03d.png"% (k+zoomOutFrames+disappFrames+dNthFrames+rotMeshFrames+skipFrames)
    #~ bpy.data.scenes["Scene"].render.resolution_x = resW #perhaps set resolution in code
    #~ bpy.data.scenes["Scene"].render.resolution_y = resH
    #~ bpy.data.scenes["Scene"].render.resolution_percentage = resPerc
    #~ bpy.ops.render.render( write_still=True )
    #~ bpy.data.objects["ShapeIndexedFaceSet.%03d"% (k+1)].hide_render=1     #hide current version for render


#=======================================================================
#~ for k in range(nFrames):
    #~ timeDesc.data.body = "t = %5.2f s"% (k*tStep)
    #~ bpy.data.objects["ShapeIndexedFaceSet.%03d"% (k+1)].hide_render=0    #unhide current version for render
    #~ bpy.data.scenes["Scene"].render.filepath = imDir+"animation_%03d.png"% (k)
    #~ bpy.data.scenes["Scene"].render.resolution_x = resW #perhaps set resolution in code
    #~ bpy.data.scenes["Scene"].render.resolution_y = resH
    #~ bpy.data.scenes["Scene"].render.resolution_percentage = resPerc
    #~ bpy.ops.render.render( write_still=True )
    #~ bpy.data.objects["ShapeIndexedFaceSet.%03d"% (k+1)].hide_render=1     #hide current version for render
