#!/usr/bin/python

#FILE DESCRIPTION=======================================================
#~ Simple python script to enable some parametrization of the mesh
#~ creation for the case of film flow down an inclined plate
#~ (interFoam used as a solver)
#~ 
#~ - Adds a grading in z-direction to reduce the number of cells
#~ - number of cells is based on the dense block cell size (input)


#LICENSE================================================================
#  fblockMeshGen.py
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
#AUXILIARY FUNCTIONS==================================================== 
def addHoleX(distHX,diamHEff,vert):
	# function to add vertices for 1 hole in x-direction
	cX,cY,cZ = vert[-1]													#get position of the last vertex
	cX 	     = cX + distHX												#move by distHX
	vert.append([cX,cY,cZ])												#append hole starting vertex
	cX 	     = cX + diamHEff											#move by diamHEff
	vert.append([cX,cY,cZ])												#append hole ending vertex
	return vert															#return updated vertex list
def addHolesCol(distHX,distHY,diamHEff,nHolesX,vert):
	# function to create vertices for a whole column (x-direction)
	x0,y0,z0 = vert[0]													#initial node
	cX,cY,cZ = vert[-1]													#current position
	# -- create left sides of the holes
	cY 		 = cY + distHY
	vert.append([x0,cY,cZ])												#starting vertex
	vert = addHoleX(distHX/2,diamHEff,vert)								#second vertex (only 0.5 distHX)
	for i in range(1,nHolesX):
		vert = addHoleX(distHX,diamHEff,vert)
	cX 		 = vert[-1][0]												#current position
	vert.append([vert[-1][0]+distHX/2,cY,cZ])							#ending vertex
	# -- create right sides of the holes
	cY 		 = cY + diamHEff
	vert.append([x0,cY,cZ])												#starting vertex
	vert = addHoleX(distHX/2,diamHEff,vert)								#second vertex (only 0.5 distHX)
	for i in range(1,nHolesX):
		vert = addHoleX(distHX,diamHEff,vert)
	vert.append([vert[-1][0]+distHX/2,cY,cZ])							#ending vertex
	return vert
def writeArcs(i,j,diamH,diamHEff,nVert,vert):
	#function to write arcs based on vertex position and hole pars
	#returns list of strings (arcs to write to blockMeshDict)
	cX,cY,cZ = vert[i]													#get position of the base vertex
	# left arc
	aX = cX + diamHEff/2
	aY = cY - (diamH-diamHEff)/2
	strList = [None]*4													#list initialization
	strList[0] = "\tarc\t%i\t%i\t(%5.5f %5.5f %5.5f)\n"%(i,i+1,aX,aY,cZ)
	# bottom arc
	aX = cX + (diamH+diamHEff)/2
	aY = cY + diamHEff/2
	strList[1] = "\tarc\t%i\t%i\t(%5.5f %5.5f %5.5f)\n"%(i+1,j+1,aX,aY,cZ)
	# right arc
	aX = cX + diamHEff/2
	aY = cY + (diamH+diamHEff)/2
	strList[2] = "\tarc\t%i\t%i\t(%5.5f %5.5f %5.5f)\n"%(j+1,j,aX,aY,cZ)
	# top arc
	aX = cX - (diamH-diamHEff)/2
	aY = cY + diamHEff/2
	strList[3] = "\tarc\t%i\t%i\t(%5.5f %5.5f %5.5f)\n"%(j,i,aX,aY,cZ)
	return strList
#FUNCTION INTERFACE BLOCK===============================================
def fblockMeshGen(caseDir,												#need to specify case directory
	hI 		 = 0.4e-3,													#liquid inlet height
	geomSize = [50e-3,60e-3,7e-3],										#width, length and height of the geometry (in m)
	cellSize = [1e-3,1e-3,0.2e-3],										#width, length and height of on cell in dense block (in m),
	holePars = [3e-3,10e-3,10e-3],										#diameter of a hole and distance between holes in X and Y directions
	spGrad 	 = 10,														#grading in zDir of sparse block
	mScale 	 = 1):

	#IMPORT BLOCK=======================================================
	import os
	import copy
	import math
	
	#===================================================================
	#							EDITABLE
	#===================================================================
	
	#-------------------------------------------------------------------
	# GEOMETRY DATA
	#-------------------------------------------------------------------
	
	# central point
	x0, y0, z0 				= 0.0, 0.0, 0.0
	
	#-------------------------------------------------------------------
	# mesh grading
	grDX, grDY, grDZ = 1.0, 1.0, 1.0									#grading in dense block
	grSX, grSY, grSZ = 1.0, 1.0, 1.0									#grading in sparse block
	
	
	#===================================================================
	#							DO NOT EDIT
	#===================================================================
	
	# get the dimensions of the whole geometry and one cell
	aG,lG,hG  = geomSize
	hG		  = hG/2													#backward code compatibility
	dA,dL,dH  = cellSize
	# get parameters of the plate perforation
	diamH,distHX,distHY = holePars
	distHY = distHY/2													#I need to create twice as many holes than specified (for the translation and fake holes)
	diamHEff  = math.sqrt(2)/2*diamH									#"effective hole size"
	
	# auxiliary variables for geometry creation
	hDCoeff   = 3														#how high should the dense block be (relative to inlet height)
	zCoordVec = [z0,z0+hI,z0+hDCoeff*hI,z0+hG,
				 z0+2*hG-hDCoeff*hI,z0+2*hG-hI,z0+2*hG]			    	#levels in z direction
	#~ zCoordVec = [z0]						    #levels in z direction
	nLrs   	  = len(zCoordVec)										    #number of levels in z direction
	
	# calculate number of holes in each direction and correct the distances
	# between the holes to get a uniform perforation pattern
	alphaX,alphaY = distHX/diamHEff,distHY/diamHEff
	nHolesX   = math.floor(lG/(diamHEff*(1+alphaX)))					#number of holes in x-direction
	nHolesY   = math.floor(aG/(diamHEff*(1+alphaY)))					#number of holes in y-direction
	distHX	  = lG/nHolesX-diamHEff										#corrected distance in x-direction
	distHY	  = aG/nHolesY-diamHEff										#corrected distance in y-direction
	nHolesX,nHolesY = int(nHolesX),int(nHolesY)							#conversion to integers
	nVertX,nVertY   = 2*nHolesX+2,2*nHolesY+2							#number of vertices in x,y-direction
	nVert 	  = nVertX*nVertY											#number of vertices in 1 layer
	
	# get the number of cells in X-Y planes (between holes, marginal and holes)
	nCellsBX,nCellsBY 		= int(math.ceil(distHX/dL)),int(math.ceil(distHY/dL))
	nCellsMX,nCellsMY 		= int(math.floor(nCellsBX/2)),int(math.floor(nCellsBY/2))
	nCellsHX,nCellsHY		= int(math.ceil(diamHEff/dL)),int(math.ceil(diamHEff/dA))
	# create vectors with number of cells for easy block creation
	nCellsXVec				= [nCellsBX,nCellsHX]*nHolesX				#repeated number of cells
	nCellsXVec[0]			= nCellsMX									#start with 1/2 of a plate block
	nCellsXVec.append(nCellsMX)											#end with 1/2 of a plate block
	nCellsYVec				= [nCellsBY,nCellsHY]*nHolesY				#repeated number of cells
	nCellsYVec[0]			= nCellsMY									#start with 1/2 of a plate block
	nCellsYVec.append(nCellsMY)											#end with 1/2 of a plate block
	
	# get the number of cells in Z direction (different blocks)
	nCellsZ    = int(math.ceil(hI/dH))
	nCellsZS   = int(math.ceil(2*(hG-hDCoeff*hI)/(dH*(1+spGrad))))		#get number of cells in sparse block
	# Note: grading factor in blockMesh is defined as the ratio of the
	#		last to first cell size (hjasak) -> I can get the number of
	#		cells from the sum of arithmetic series
	nCellsZVec = [nCellsZ,(hDCoeff-1)*nCellsZ,nCellsZS,
				  nCellsZS,(hDCoeff-1)*nCellsZ,nCellsZ]					#vector with number of cells in zDir
	
	zGradVec   = [1.0,1.0,float(spGrad),1/float(spGrad),1.0,1.0]
	
	# define matrix of vertices and nodes for arcs
	vert = []
	arcs = []															#not really used
	
	for zCoord in zCoordVec:											#this is quite simple
		# -- plate left side
		vert.append([x0     ,y0    ,zCoord])
		vert = addHoleX(distHX/2,diamHEff,vert)							#second vertex, only 0.5 distHX
		for j in range(1,nHolesX):
			vert = addHoleX(distHX,diamHEff,vert)
		vert.append([vert[-1][0]+distHX/2,y0,zCoord])
		# -- plate middle
		vert = addHolesCol(distHX,distHY/2,diamHEff,nHolesX,vert)		#first column
		for i in range(1,nHolesY):
			vert = addHolesCol(distHX,distHY,diamHEff,nHolesX,vert)
		# -- plate right side
		vert.append([x0     ,y0+aG    ,zCoord])
		vert = addHoleX(distHX/2,diamHEff,vert)							#second vertex, only 0.5 distHX
		for j in range(1,nHolesX):
			vert = addHoleX(distHX,diamHEff,vert)
		vert.append([vert[-1][0]+distHX/2,y0+aG,zCoord])

	lablsV = []															#list of vertices labels
	for i in range(nLrs):
		lablsV.append([range(i*nVert+j*nVertX,i*nVert+(j+1)*nVertX) for j in range(0,nVertY)])
		
	for value in lablsV:
	    # Print each row's length and its elements.
	    print(value)
	
	#===================================================================

	#===================================================================
	#CREATE FILE AND WRITE THE DATA IN==================================
	bMD = open(caseDir + './constant/polyMesh/blockMeshDict','w')		#open file for writing
	
	#-----------------------------------------------------------------------
	# write the headline
	bMD.write('/*--------------------------------*- C++ -*----------------------------------*\ \n')
	bMD.write('| ========                 |                                                 | \n')
	bMD.write('| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           | \n')
	bMD.write('|  \\    /   O peration     | Version:  2.3.0                                 | \n')
	bMD.write('|   \\  /    A nd           | Web:      www.OpenFOAM.org                      | \n')
	bMD.write('|    \\/     M anipulation  |                                                 | \n')
	bMD.write('\*---------------------------------------------------------------------------*/ \n')
	
	# write file description
	bMD.write('FoamFile \n')
	bMD.write('{ \n \t version \t 2.0; \n \t format \t ascii; \n')
	bMD.write(' \t class \t\t dictionary; \n \t location \t "constant/polyMesh";\n \t object \t blockMeshDict; \n} \n')
	bMD.write('// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * // \n\n')
	
	#-------------------------------------------------------------------
	# convert to metres
	bMD.write('convertToMeters \t' + repr(mScale) + '; \n\n')
	
	#-------------------------------------------------------------------
	# write vertices
	bMD.write('vertices \n( \n')
	k = 0
	for row in vert:
	    bMD.write('\t ( ' + ' '.join(str(e) for e in row) + ' )\t//' + repr(k) + '\n')
	    k = k+1
	bMD.write('); \n\n')
	#-------------------------------------------------------------------
	# write edges
	bMD.write('edges \n( \n')
	for i in range(1,nVertX-1,4):										#only holes			
		# -- odd rows	
		for j in range(1,nVertY-1,4):
			strList = writeArcs(lablsV[0][j][i],lablsV[0][j+1][i],diamH,diamHEff,nVert,vert)		#bottom arcs
			for arc in strList:
				bMD.write(arc)
			strList = writeArcs(lablsV[-1][j][i],lablsV[-1][j+1][i],diamH,diamHEff,nVert,vert)		#top arcs
			for arc in strList:
				bMD.write(arc)
		# -- even rows
		for j in range(3,nVertY-3,4):
			strList = writeArcs(lablsV[0][j][i+2],lablsV[0][j+1][i+2],diamH,diamHEff,nVert,vert)		#bottom arcs
			for arc in strList:
				bMD.write(arc)
			strList = writeArcs(lablsV[-1][j][i+2],lablsV[-1][j+1][i+2],diamH,diamHEff,nVert,vert)		#top arcs
			for arc in strList:
				bMD.write(arc)
	bMD.write('); \n\n')
	#-------------------------------------------------------------------
	# write blocks
	bMD.write('blocks \n( \n')
	for i in range(nLrs-1):												#each layer in z-direction
		for j in range(len(nCellsYVec)):								#each layer in y-direction
			for k in range(len(nCellsXVec)):							#each layer in x-direction
				bMD.write('\t hex \n')
				bMD.write('\t \t ( '
						  +
						  ' '.join(str(e) for e in lablsV[i][j][k:k+2])
						  + ' ' + 
						  ' '.join(str(e) for e in list(reversed(lablsV[i][j+1][k:k+2])))#automatic indexing
						  + ' ' + 
						  ' '.join(str(e) for e in lablsV[i+1][j][k:k+2])
						  + ' ' + 
						  ' '.join(str(e) for e in list(reversed(lablsV[i+1][j+1][k:k+2])))
						  +
						  ' ) \n'
						  )
				bMD.write('\t \t ( ' + repr(nCellsXVec[k]) + ' ' + repr(nCellsYVec[j]) + ' ' + repr(nCellsZVec[i]) + ' ) ')
				bMD.write('\t simpleGrading ')
				bMD.write('\t ( ' + repr(1.0) + ' ' + repr(1.0) + ' ' + repr(zGradVec[i]) + ' ) \n')
	bMD.write('); \n\n')
	#-------------------------------------------------------------------
	# write boundaries
	bMD.write('boundary \n( \n')
	# -- inlet
	bMD.write('\tinlet \n\t{ \n')
	bMD.write('\ttype patch; \n')
	bMD.write('\tfaces \n \t(\n')
	for i in range(nVertY-1):
		wrVec = [#not exactly top notch programming, but it should be clear what I did
					lablsV[0][i][0],
					lablsV[1][i][0],
					lablsV[1][i+1][0],
					lablsV[0][i+1][0],
				]
		bMD.write('\t\t( ' 
			 + 
			 ' '.join(str(e) for e in wrVec) 
			 + 
			 ' ) \n'
			 )            
	bMD.write('\t);\n\t} \n\n')
	# -- gasOutlet
	bMD.write('\tgasOutlet \n\t{ \n')
	bMD.write('\ttype patch; \n')
	bMD.write('\tfaces \n \t(\n')
	for i in range(1,nLrs-1):
		for j in range(nVertY-1):
			wrVec = [#not exactly top notch programming, but it should be clear what I did
						lablsV[i][j][0],
						lablsV[i+1][j][0],
						lablsV[i+1][j+1][0],
						lablsV[i][j+1][0],
					]
			bMD.write('\t\t( ' 
				 + 
				 ' '.join(str(e) for e in wrVec) 
				 + 
				 ' ) \n'
				 )            
	bMD.write('\t);\n\t} \n\n')
	# -- outlet
	bMD.write('\toutlet \n\t{ \n')
	bMD.write('\ttype patch; \n')
	bMD.write('\tfaces \n \t(\n')
	for i in range(nLrs-1):
		for j in range(nVertY-1):
			wrVec = [#not exactly top notch programming, but it should be clear what I did
						lablsV[i][j][-1],
						lablsV[i+1][j][-1],
						lablsV[i+1][j+1][-1],
						lablsV[i][j+1][-1],
					]
			bMD.write('\t\t( ' 
				 + 
				 ' '.join(str(e) for e in wrVec) 
				 + 
				 ' ) \n'
				 )            
	bMD.write('\t);\n\t} \n\n')
	# -- sides
	bMD.write('\tsides \n\t{ \n')
	bMD.write('\ttype wall; \n')
	bMD.write('\tfaces \n \t(\n')
	for i in range(nLrs-1):
		for j in range(nVertX-1):
			wrVec = []
			wrVec.append([#not exactly top notch programming, but it should be clear what I did
						lablsV[i][0][j],
						lablsV[i][0][j+1],
						lablsV[i+1][0][j+1],
						lablsV[i+1][0][j],
					])
			wrVec.append([#not exactly top notch programming, but it should be clear what I did
						lablsV[i][-1][j],
						lablsV[i][-1][j+1],
						lablsV[i+1][-1][j+1],
						lablsV[i+1][-1][j],
					])
			for wr in wrVec:
				bMD.write('\t\t( ' 
					 + 
					 ' '.join(str(e) for e in wr) 
					 + 
					 ' ) \n'
					 )            
	bMD.write('\t);\n\t} \n\n')
	# -- plate (both top and bottom are plates)
	bMD.write('\tplate \n\t{ \n')
	bMD.write('\ttype wall; \n')
	bMD.write('\tfaces \n \t(\n')
	wrVec = []
	for k in [0,-1]:
		for j in range(0,nVertX-1,2):									#no holes skipped				
			for i in range(0,nVertY-1,1):
				wrVec.append([
						lablsV[k][i][j],
						lablsV[k][i+1][j],
						lablsV[k][i+1][j+1],
						lablsV[k][i][j+1],
					])
		for j in range(1,nVertX-1,2):									#skipping holes				
			for i in range(0,nVertY-1,2):
				wrVec.append([
						lablsV[k][i][j],
						lablsV[k][i+1][j],
						lablsV[k][i+1][j+1],
						lablsV[k][i][j+1],
					])
		# -- fake holes
		for j in range(1,nVertX-1,4):										#only holes		
			# -- odd rows
			for i in range(3,nVertY-1,4):
				wrVec.append([
						lablsV[k][i][j],
						lablsV[k][i+1][j],
						lablsV[k][i+1][j+1],
						lablsV[k][i][j+1],
					])
			# -- even rows
			for i in range(1,nVertY-1,4):
				wrVec.append([
						lablsV[k][i][j+2],
						lablsV[k][i+1][j+2],
						lablsV[k][i+1][j+3],
						lablsV[k][i][j+3],
					])
	for wr in wrVec:
		bMD.write('\t\t( ' 
			 + 
			 ' '.join(str(e) for e in wr) 
			 + 
			 ' ) \n'
			 )              
	bMD.write('\t);\n\t} \n\n')
	# -- bottom holes
	bMD.write('\tholesBottomPrep \n\t{ \n')
	bMD.write('\ttype patch; \n')
	bMD.write('\tfaces \n \t(\n')
	wrVec = []
	for j in range(1,nVertX-1,4):										#only holes	
		# -- odd rows			
		for i in range(1,nVertY-1,4):
			wrVec.append([
					lablsV[0][i][j],
					lablsV[0][i+1][j],
					lablsV[0][i+1][j+1],
					lablsV[0][i][j+1],
				])
		# -- even rows			
		for i in range(3,nVertY-3,4):
			wrVec.append([
					lablsV[0][i][j+2],
					lablsV[0][i+1][j+2],
					lablsV[0][i+1][j+3],
					lablsV[0][i][j+3],
				])
	for wr in wrVec:
		bMD.write('\t\t( ' 
			 + 
			 ' '.join(str(e) for e in wr) 
			 + 
			 ' ) \n'
			 )
	bMD.write('\t);\n\t} \n\n')
	# -- top holes
	bMD.write('\tholesTopPrep \n\t{ \n')
	bMD.write('\ttype patch; \n')
	bMD.write('\tfaces \n \t(\n')
	wrVec = []
	for j in range(1,nVertX-1,4):										#only holes		
		# -- odd rows
		for i in range(1,nVertY-1,4):
			wrVec.append([
					lablsV[-1][i][j],
					lablsV[-1][i+1][j],
					lablsV[-1][i+1][j+1],
					lablsV[-1][i][j+1],
				])
		# -- even rows
		for i in range(3,nVertY-3,4):
			wrVec.append([
					lablsV[-1][i][j+2],
					lablsV[-1][i+1][j+2],
					lablsV[-1][i+1][j+3],
					lablsV[-1][i][j+3],
				])
	for wr in wrVec:
		bMD.write('\t\t( ' 
			 + 
			 ' '.join(str(e) for e in wr) 
			 + 
			 ' ) \n'
			 )
	bMD.write('\t);\n\t} \n\n')
	bMD.write('); \n\n')
	#-------------------------------------------------------------------
	# -- merge patch pairs
	bMD.write('mergePatchPairs \n( \n')
	bMD.write('); \n\n')
	#-------------------------------------------------------------------
	# footline
	bMD.write('// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * // \n\n')
	#-------------------------------------------------------------------
	# close file
	bMD.close()

	return;
