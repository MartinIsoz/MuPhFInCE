#!/usr/bin/python

#FILE DESCRIPTION=======================================================
#~ Simple python script to enable some parametrization of the mesh
#~ creation for the case of rivulet spreading down an inclined plate
#~ (interFoam used as a solver)
#~ 
#~ - 


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

#FUNCTION INTERFACE BLOCK
def fblockMeshGen(caseDir,												#need to specify case directory
	x0 = 0.0,y0 = 0.0, z0 = 0.0,
	cL = 300.0e-3,cW = 75.0e-3, cH = 10.0e-3,iH = 10.0e-3, tL = 10.0e-3,
	dbW= 40.0e-3,nDiv = 3,d0 = 1,
	nCellsXDL = 300, nCellsXDS = 20, nCellsYD = 50, nCellsZD = 50,
	nCellsXSL = 60, nCellsXSS = 10, nCellsYS = 20, nCellsZS = 10, nCellsZI = 40,
	mScale = 1):

	#IMPORT BLOCK=======================================================
	import os
	import copy
	import math
	
	#===================================================================
	#							EDITABLE
	#===================================================================
	
	#GET THE DATA=======================================================
	
	#-------------------------------------------------------------------
	# GEOMETRY DATA
	#-------------------------------------------------------------------
	
	# central point
	x0, y0, z0 				= 0.0, 0.0, 0.0
	# geometry dimensions
	#~ cL, cW, cH, iH, tL		= 300.0e-3, 40.0e-3, 3.0e-3, 10.0e-3, 10.0e-3
	iW 						= math.sqrt(3)/3*tL							#inlet half-width
	# width of the dense block (to contain the rivulet)
	#~ dbW 					= 20.0e-3
	# in which part (from the center point) should be the inlet divided
	#~ nDiv 					= 3
	
	# length scale - cell height
	#~ d0 						= 1
	cL, cW, cH, iH, iW, tL 	= cL/d0, cW/d0, cH/d0, iH/d0, iW/d0, tL/d0
	dbW 					= dbW/d0
	
	#-------------------------------------------------------------------
	# MESH DATA
	#-------------------------------------------------------------------
	# number of cells in each direction for each part of the mesh
	#~ nCellsXDL = 300	#number of cells in dense long blocks - xDirection
	#~ nCellsXDS = 20	#number of cells in dense short blocks - xDirection
	#~ nCellsYD  = 30	#number of cells in dense long & short blocks - yDirection
	#~ nCellsZD  = 20 	#number of cells in dense long & short blocks - zDirection
	#~ 
	#~ nCellsXSL = nCellsXDL/5	#number of cells in sparse long blocks - xDirection
	#~ nCellsXSS = 10	#number of cells in sparse short blocks - xDirection
	#~ nCellsYS  = 10	#number of cells in sparse long & short blocks - yDirection
	#~ nCellsZS  = 10 	#number of cells in sparse long & short blocks - zDirection
	#~ 
	#~ nCellsZI  = 40  #number of cells in inlet z direction
	
	# auxiliary lists
	nCellsXS  = [nCellsXSS,nCellsXSL]
	nCellsZT  = [nCellsZI,nCellsZD]
	
	#-------------------------------------------------------------------
	# mesh grading
	grDX, grDY, grDZ = 1.0, 1.0, 1.0									#grading in dense block
	grSX, grSY, grSZ = 1.0, 1.0, 1.0									#grading in sparse block
	
	# scale (to meters)
	#~ mScale = 1
	
	#===================================================================
	#							DO NOT EDIT
	#===================================================================
	
	# define the central line on ground floor
	tLGrF 				= (
							[
								[x0-tL,y0,z0],
								[x0, y0, z0],
								[x0+cL,y0,z0],
							]
						  )
	# define the central line on basement and top floors
	tLBsF 				= copy.deepcopy(tLGrF)							#initiate lists
	tLTpF 				= copy.deepcopy(tLGrF) 							#DNK why deepcopy is needed but...
	
	for i in range(len(tLGrF)):
		tLBsF[i][2]   	= tLBsF[i][2] - iH								#lower by inlet height
		tLTpF[i][2]   	= tLTpF[i][2] + cH								#higher by cell height
	
	# put all the central line together
	cLVerts 			= [[]]*3										#initiate the list
	cLVerts[0]		 	= copy.deepcopy(tLBsF)							#each field is a list of its own
	cLVerts[1] 			= copy.deepcopy(tLGrF)
	cLVerts[2] 			= copy.deepcopy(tLTpF)
	    
	# create right sides of the geometry/dense block - move all by +-cW, +-dbW
	rSVerts 			= copy.deepcopy(cLVerts)						#copy central line
	lSVerts 			= copy.deepcopy(cLVerts)
	rDBVerts 			= copy.deepcopy(cLVerts)
	lDBVerts 			= copy.deepcopy(cLVerts)
	for i in range(len(cLVerts)):
		for j in range(len(cLVerts[i])):
			rSVerts[i][j][1] 	= rSVerts[i][j][1] + cW
			lSVerts[i][j][1] 	= lSVerts[i][j][1] - cW
			rDBVerts[i][j][1] 	= rDBVerts[i][j][1] + dbW
			lDBVerts[i][j][1] 	= lDBVerts[i][j][1] - dbW
	
	#~ # test the output
	#~ print('Central line================')
	#~ for value in cLVerts:
	    #~ # Print each row's length and its elements.
	    #~ print(value)
	#~ print('Geom sides==================')   
	#~ for value in rSVerts:
	    #~ # Print each row's length and its elements.
	    #~ print(value)
	#~ print('----------------------------')
	#~ for value in lSVerts:
	    #~ # Print each row's length and its elements.
	    #~ print(value)
	#~ print('Dense block sides===========')   
	#~ for value in rDBVerts:
	    #~ # Print each row's length and its elements.
	    #~ print(value)
	#~ print('----------------------------')
	#~ for value in lDBVerts:
	    #~ # Print each row's length and its elements.
	    #~ print(value)
	    
	# define matrix of vertices
	vert 		= []													#initiate the list of vertices
	
	# convert the already done lists
	# -- left side
	for i in range(len(cLVerts)):
		for j in range(len(cLVerts[i])):
			vert.extend(lSVerts[i][j:j+1])
			
	# -- left side sparse-dense block interface
	for k in [0,1]:
		for i in range(len(cLVerts)):
			for j in range(len(cLVerts[i])):
				vert.extend(lDBVerts[i][j:j+1])	
				
	# -- centerline
	for i in range(len(cLVerts)):
		for j in range(len(cLVerts[i])):
			vert.extend(cLVerts[i][j:j+1])
			
	# -- right side sparse-dense block interface
	for k in [0,1]:														#each of these nodes is needed 2x
		for i in range(len(cLVerts)):
			for j in range(len(cLVerts[i])):
				vert.extend(rDBVerts[i][j:j+1])
	
	# -- right side
	for i in range(len(cLVerts)):
		for j in range(len(cLVerts[i])):
			vert.extend(rSVerts[i][j:j+1])
			
			
	# -- left side inlet
	vert.append([x0-tL,y0-iW,z0-iH])
	vert.append([x0-tL,y0-iW,z0])
	vert.append([x0-tL,y0-iW,z0+cH])
				
	# -- right side inlet
	vert.append([x0-tL,y0+iW,z0-iH])
	vert.append([x0-tL,y0+iW,z0])
	vert.append([x0-tL,y0+iW,z0+cH])		
			
	# -- auxiliary vertices in the inlet area (left side)
	# /needed to mitigate the extremely small cells
	vert.append([x0-nDiv*tL/nCellsXDS,
				 y0-math.sqrt(3)/3*nDiv*tL/nCellsXDS,
				 z0-iH
				])
	vert.append([x0-nDiv*tL/nCellsXDS,
				 y0-math.sqrt(3)/3*nDiv*tL/nCellsXDS,
				 z0
				])
	vert.append([x0-nDiv*tL/nCellsXDS,
				 y0-math.sqrt(3)/3*nDiv*tL/nCellsXDS,
				 z0+cH
				])	
	# /I need two sets for patches merging/
	vert.append([x0-nDiv*tL/nCellsXDS,
				 y0-math.sqrt(3)/3*nDiv*tL/nCellsXDS,
				 z0-iH
				])
	vert.append([x0-nDiv*tL/nCellsXDS,
				 y0-math.sqrt(3)/3*nDiv*tL/nCellsXDS,
				 z0
				])
	vert.append([x0-nDiv*tL/nCellsXDS,
				 y0-math.sqrt(3)/3*nDiv*tL/nCellsXDS,
				 z0+cH
				])									
	
	
	# -- auxiliary vertices in the inlet area (right side)
	# /needed to mitigate the extremely small cells
	vert.append([x0-nDiv*tL/nCellsXDS,
				 y0+math.sqrt(3)/3*nDiv*tL/nCellsXDS,
				 z0-iH
				])
	vert.append([x0-nDiv*tL/nCellsXDS,
				 y0+math.sqrt(3)/3*nDiv*tL/nCellsXDS,
				 z0
				])
	vert.append([x0-nDiv*tL/nCellsXDS,
				 y0+math.sqrt(3)/3*nDiv*tL/nCellsXDS,
				 z0+cH
				])
	# /I need two sets for patches merging/
	vert.append([x0-nDiv*tL/nCellsXDS,
				 y0+math.sqrt(3)/3*nDiv*tL/nCellsXDS,
				 z0-iH
				])
	vert.append([x0-nDiv*tL/nCellsXDS,
				 y0+math.sqrt(3)/3*nDiv*tL/nCellsXDS,
				 z0
				])
	vert.append([x0-nDiv*tL/nCellsXDS,
				 y0+math.sqrt(3)/3*nDiv*tL/nCellsXDS,
				 z0+cH
				])		
	
	
	
	print('Vertices====================')
	for value in vert:
	    # Print each row's length and its elements.
	    print(value)
	
	# create labels for the vertices
	nGroups 	= 5+2													#number of vertical subgroups
	labls		= []													#initiate the list of labels
	k 			= 0
	for i in range(nGroups):											#first nGroups are the same
		labls.append(range(k,k+len(cLVerts)*len(cLVerts[0])))
		k  		= k+len(cLVerts)*len(cLVerts[0])
		
	for i in range(2):
		labls.append(range(k,k+3))
		k 		= k+3
		
	for i in range(2):
		labls.append(range(k,k+6))
		k 		= k+6	
		
	
	print('Labels====================')
	for value in labls:
	    # Print each row's length and its elements.
	    print(value)	
	
	#CREATE FILE AND WRITE THE DATA IN==================================
	bMD = open(caseDir + './constant/polyMesh/blockMeshDict','w')		#open file for writing
	
	#-------------------------------------------------------------------
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
	bMD.write(' \t class \t\t dictionary; \n \t object \t blockMeshDict; \n} \n')
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
	
	#-----------------------------------------------------------------------
	# write blocks
	bMD.write('blocks \n( \n')
	# -- sparse blocks
	# --: those block are created in order: top left, cell left, top right, cell right
	descList = ['left','right','top','cell']
	for i in [0,5]:
		for j in [3,4]:
			bMD.write('\t hex // sparse ' + descList[i/5] + ' ' + descList[j-1] + '\n')
			bMD.write('\t \t ( ' 
						+ 
						' '.join(str(e) for e in labls[i][j:j+2]) 
						+ 
						' '
						+ 
						' '.join(str(e) for e in labls[i+1][j+1:j-1:-1]) 
						+ 
						' '
						+ 
						' '.join(str(e) for e in labls[i][j+3:j+5]) 
						+ 
						' '
						+ 
						' '.join(str(e) for e in labls[i+1][j+4:j+2:-1]) 
						+ 
						' ) \n'
						)
			bMD.write('\t \t ( ' + repr(nCellsXS[j-3]) + ' ' + repr(nCellsYS) + ' ' + repr(nCellsZS) + ' ) ')
			bMD.write('\t simpleGrading ')
			bMD.write('\t ( ' + repr(grSX) + ' ' + repr(grSY) + ' ' + repr(grSZ) + ' ) \n')
	# -- dense blocks - cell
	# --: those blocks are created from left to right
	for i in [2,3]:
		for j in [4]:
			bMD.write('\t hex // dense ' + descList[i-2] + ' ' + descList[j-1] + '\n')
			bMD.write('\t \t ( ' 
						+ 
						' '.join(str(e) for e in labls[i][j:j+2]) 
						+ 
						' '
						+ 
						' '.join(str(e) for e in labls[i+1][j+1:j-1:-1]) 
						+ 
						' '
						+ 
						' '.join(str(e) for e in labls[i][j+3:j+5]) 
						+ 
						' '
						+ 
						' '.join(str(e) for e in labls[i+1][j+4:j+2:-1]) 
						+ 
						' ) \n'
						)
			bMD.write('\t \t ( ' + repr(nCellsXDL) + ' ' + repr(nCellsYD) + ' ' + repr(nCellsZD) + ' ) ')
			bMD.write('\t simpleGrading ')
			bMD.write('\t ( ' + repr(grSX) + ' ' + repr(grSY) + ' ' + repr(grSZ) + ' ) \n')
	# -- dense blocks - top
	# --: those blocks are created from left to right
	#	  these are little bit more tricky - there is a triangular inlet
	bMD.write('\t hex // dense ' + descList[0] + ' ' + descList[2] + '\n')#left side
	bMD.write('\t \t ( ' 
				+ 
				' '.join(str(e) for e in labls[2][3:5]) 
				+ 
				' '
				+ 
				repr(labls[3][4]) 
				+ 
				' '
				+ 
				repr(labls[7][1])
				+ 
				' '
				+ 
				' '.join(str(e) for e in labls[2][6:8]) 
				+ 
				' '
				+ 
				repr(labls[3][7]) 
				+ 
				' '
				+ 
				repr(labls[7][2])
				+ 
				' ) \n'
				)
	bMD.write('\t \t ( ' + repr(nCellsXDS) + ' ' + repr(nCellsYD) + ' ' + repr(nCellsZD) + ' ) ')
	bMD.write('\t simpleGrading ')
	bMD.write('\t ( ' + repr(grSX) + ' ' + repr(grSY) + ' ' + repr(grSZ) + ' ) \n')
	bMD.write('\t hex // dense ' + descList[1] + ' ' + descList[2] + '\n')#right side
	bMD.write('\t \t ( ' 
				+ 
				repr(labls[8][1]) 
				+ 
				' '
				+ 
				repr(labls[3][4]) 
				+ 
				' '
				+ 
				' '.join(str(e) for e in labls[4][4:2:-1])
				+ 
				' '
				+ 
				repr(labls[8][2]) 
				+ 
				' '
				+ 
				repr(labls[3][7]) 
				+ 
				' '
				+ 
				' '.join(str(e) for e in labls[4][7:5:-1])
				+ 
				' ) \n'
				)
	bMD.write('\t \t ( ' + repr(nCellsXDS) + ' ' + repr(nCellsYD) + ' ' + repr(nCellsZD) + ' ) ')
	bMD.write('\t simpleGrading ')
	bMD.write('\t ( ' + repr(grSX) + ' ' + repr(grSY) + ' ' + repr(grSZ) + ' ) \n')
	# -- inlet and over the inlet blocks
	# -- first block (the top)
	for i in [0,1]:
		bMD.write('\t hex \n')
		bMD.write('\t \t ( ' 
					+ 
					repr(labls[7][0+i]) + ' ' + repr(labls[9][0+i]) 
					+ 
					' '
					+ 
					repr(labls[10][0+i]) + ' ' + repr(labls[8][0+i]) 
					+ 
					' '
					+ 
					repr(labls[7][1+i]) + ' ' + repr(labls[9][1+i]) 
					+ 
					' '
					+ 
					repr(labls[10][1+i]) + ' ' + repr(labls[8][1+i]) 
					+ 
					' ) \n'
					)
		bMD.write('\t \t ( ' + repr(nCellsXDS-nDiv) + ' ' + repr(int(math.floor(nCellsXDS/2))) + ' ' + repr(nCellsZT[i]) + ' ) ')
		bMD.write('\t simpleGrading ')
		bMD.write('\t ( ' + repr(grSX) + ' ' + repr(grSY) + ' ' + repr(grSZ) + ' ) \n')
	# -- last block (the tip)
	for i in [0,1]:
		bMD.write('\t hex \n')
		bMD.write('\t \t ( ' 
					+ 
					repr(labls[-2][-3+i]) + ' ' + repr(labls[3][1+3*i]) 
					+ 
					' '
					+ 
					repr(labls[3][1+3*i]) + ' ' + repr(labls[-1][-3+i]) 
					+ 
					' '
					+ 
					repr(labls[-2][-2+i]) + ' ' + repr(labls[3][4+3*i]) 
					+ 
					' '
					+ 
					repr(labls[3][4+3*i]) + ' ' + repr(labls[-1][-2+i]) 
					+ 
					' ) \n'
					)
		bMD.write('\t \t ( ' + repr(nDiv) + ' ' + repr(nDiv) + ' ' + repr(nCellsZT[i]) + ' ) ')
		bMD.write('\t simpleGrading ')
		bMD.write('\t ( ' + repr(grSX) + ' ' + repr(grSY) + ' ' + repr(grSZ) + ' ) \n')
	bMD.write('); \n\n')
	
	#-------------------------------------------------------------------
	# write edges
	bMD.write('edges \n( \n')
	bMD.write('); \n\n')
	
	#-------------------------------------------------------------------
	# write boundary
	# -- note: boundaries are defined by right hand rule with thumb pointing outwards
	bMD.write('boundary \n( \n')
	# -- inlet
	bMD.write('\tinlet \n\t{ \n')
	bMD.write('\ttype patch; \n')
	bMD.write('\tfaces \n \t(\n')
	bMD.write('\t( ' 
				+ 
				repr(labls[7][0]) + ' ' + repr(labls[9][0]) 
				+ 
				' '
				+ 
				repr(labls[10][0]) + ' ' + repr(labls[8][0]) 
				+ 
				' ) \n'
				)
	bMD.write('\t( ' 
				+ 
				repr(labls[-2][-3]) + ' ' + repr(labls[3][1]) 
				+ 
				' '
				+ 
				repr(labls[3][1]) + ' ' + repr(labls[-1][-3]) 
				+ 
				' ) \n'
				)
	bMD.write('\t);\n\t} \n\n')	
	# -- outlet
	bMD.write('\toutlet \n\t{ \n')
	bMD.write('\ttype patch; \n')
	bMD.write('\tfaces \n \t(\n')
	for i in [0,2,3,5]:
		bMD.write('\t( ' 
					+ 
					repr(labls[i][5]) + ' ' + repr(labls[i+1][5]) 
					+ 
					' '
					+ 
					repr(labls[i+1][8]) + ' ' + repr(labls[i][8]) 
					+ 
					' ) \n'
					)
	bMD.write('\t);\n\t} \n\n')
	# -- plate
	bMD.write('\tplate \n\t{ \n')
	bMD.write('\ttype wall; \n')
	bMD.write('\tfaces \n \t(\n')
	for i in [0,2,3,5]:
		bMD.write('\t( ' 
					+ 
					repr(labls[i][4]) + ' ' + repr(labls[i+1][4]) 
					+ 
					' '
					+ 
					repr(labls[i+1][5]) + ' ' + repr(labls[i][5]) 
					+ 
					' ) \n'
					)
	for i in [0,5]:														#around the inlet sparse
		bMD.write('\t( ' 
					+ 
					repr(labls[i][3]) + ' ' + repr(labls[i+1][3]) 
					+ 
					' '
					+ 
					repr(labls[i+1][4]) + ' ' + repr(labls[i][4]) 
					+ 
					' ) \n'
					)
	for i in [2,4]:
		bMD.write('\t( ' 												#around the inlet dense
					+ 
					repr(labls[i][3]) + ' ' + repr(labls[-(2+4/i)][1]) 
					+ 
					' '
					+ 
					repr(labls[3][4]) + ' ' + repr(labls[i][4]) 
					+ 
					' ) \n'
					)
	bMD.write('\t);\n\t} \n\n')
	# -- walls
	bMD.write('\twalls \n\t{ \n')
	bMD.write('\ttype wall; \n')
	bMD.write('\tfaces \n \t(\n')
	for i in [0,5]:														#top inlet wall
		bMD.write('\t( ' 
					+ 
					repr(labls[i][3]) + ' ' + repr(labls[i][6]) 
					+ 
					' '
					+ 
					repr(labls[i+1][6]) + ' ' + repr(labls[i+1][3]) 
					+ 
					' ) \n'
					)
	k 	= None															#this is not the most neat trick	
	for i in [0,1]:  													#top walls (over the inlet)
		bMD.write('\t( '
					+ 
					' '.join(str(e) for e in labls[7][i:2+i]) 
					+ 
					' '
					+ 
					' '.join(str(e) for e in labls[8][1+i:k:-1]) 
					+ 
					' ) \n'
					)
		k = 0
		bMD.write('\t( ' 												#inlet - top part sides
					+ 
					repr(labls[-(4-i)][0]) + ' ' + repr(labls[-(2-i)][0]) 
					+ 
					' '
					+ 
					repr(labls[-(2-i)][1]) + ' ' + repr(labls[-(4-i)][1]) 
					+ 
					' ) \n'
					)
		bMD.write('\t( ' 												#inlet - tip sides
					+ 
					repr(labls[-(2-i)][-3]) + ' ' + repr(labls[3][1]) 
					+ 
					' '
					+ 
					repr(labls[3][4]) + ' ' + repr(labls[-(2-i)][-2]) 
					+ 
					' ) \n'
					)
	for i in [0,2]:
		bMD.write('\t( ' 												#over the inlet cell walls
					+ 
					repr(labls[2+i][3]) + ' ' + repr(labls[-4+i/2][1]) 
					+ 
					' '
					+ 
					repr(labls[-4+i/2][2]) + ' ' + repr(labls[2+i][6]) 
					+ 
					' ) \n'
					)
	for i in [0,6]:														#side cell walls
		for j in [0,1]:
			bMD.write('\t( ' 
						+ 
						repr(labls[i][3+j]) + ' ' + repr(labls[i][4+j]) 
						+ 
						' '
						+ 
						repr(labls[i][7+j]) + ' ' + repr(labls[i][6+j]) 
						+ 
						' ) \n'
						)
	bMD.write('\t);\n\t} \n\n')
	# -- atmosphere
	bMD.write('\tatmosphere \n\t{ \n')
	bMD.write('\ttype patch; \n')
	bMD.write('\tfaces \n \t(\n')
	for i in [0,2,3,5]:													#main plate
		bMD.write('\t( ' 
					+ 
					repr(labls[i][7]) + ' ' + repr(labls[i][8]) 
					+ 
					' '
					+ 
					repr(labls[i+1][8]) + ' ' + repr(labls[i+1][7]) 
					+ 
					' ) \n'
					)
	for i in [0,5]:														#around the inlet sparse
		bMD.write('\t( ' 
					+ 
					repr(labls[i][6]) + ' ' + repr(labls[i+1][6]) 
					+ 
					' '
					+ 
					repr(labls[i+1][7]) + ' ' + repr(labls[i][7]) 
					+ 
					' ) \n'
					)
	for i in [2,4]:
		bMD.write('\t( ' 												#around the inlet dense
					+ 
					repr(labls[i][6]) + ' ' + repr(labls[-(2+4/i)][2]) 
					+ 
					' '
					+ 
					repr(labls[3][7]) + ' ' + repr(labls[i][7]) 
					+ 
					' ) \n'
					)	
	bMD.write('\t( '  													#over the inlet
				+ 
				repr(labls[7][2]) + ' ' + repr(labls[9][2]) 
				+ 
				' '
				+ 
				repr(labls[10][2]) + ' ' + repr(labls[8][2]) 
				+ 
				' ) \n'
				)
	bMD.write('\t( ' 
				+ 
				repr(labls[-2][-1]) + ' ' + repr(labls[3][7]) 
				+ 
				' '
				+ 
				repr(labls[3][7]) + ' ' + repr(labls[-1][-1]) 
				+ 
				' ) \n'
				)							
	bMD.write('\t);\n\t} \n\n')
	# -- internal - to be merged - dense-sparse blocks
	k = 0
	indLst = [1,2,4,5]
	for i in ['left','right']:
		for j in ['Slave','Master']:
			bMD.write('\t' + i + j + ' \n\t{ \n')
			bMD.write('\ttype patch; \n')
			bMD.write('\tfaces \n \t(\n')
			bMD.write('\t( ' 
						+ 
						repr(labls[indLst[k]][3]) + ' ' + repr(labls[indLst[k]][4]) 
						+ 
						' '
						+ 
						repr(labls[indLst[k]][7]) + ' ' + repr(labls[indLst[k]][6]) 
						+ 
						' ) \n'
						)
			bMD.write('\t( ' 
						+ 
						repr(labls[indLst[k]][4]) + ' ' + repr(labls[indLst[k]][5]) 
						+ 
						' '
						+ 
						repr(labls[indLst[k]][8]) + ' ' + repr(labls[indLst[k]][7]) 
						+ 
						' ) \n'
						)
			bMD.write('\t);\n\t} \n\n')	
			k = k+1
	# -- internal - to be merged - inlet parts
	k = 0
	for i in ['Slave','Master']:
		bMD.write('\tinlet' + i + ' \n\t{ \n')
		bMD.write('\ttype patch; \n')
		bMD.write('\tfaces \n \t(\n')
		bMD.write('\t( ' 
					+ 
					repr(labls[-2][0+k]) + ' ' + repr(labls[-1][0+k]) 
					+ 
					' '
					+ 
					repr(labls[-1][1+k]) + ' ' + repr(labls[-2][1+k]) 
					+ 
					' ) \n'
					)
		bMD.write('\t( ' 
					+ 
					repr(labls[-2][1+k]) + ' ' + repr(labls[-1][1+k]) 
					+ 
					' '
					+ 
					repr(labls[-1][2+k]) + ' ' + repr(labls[-2][2+k]) 
					+ 
					' ) \n'
					)
		bMD.write('\t);\n\t} \n\n')
		k = k+3
	# -- internal - to be merged - over the inlet (hale mary)
	#~ descList = ['LeftMaster','RightMaster','LeftSlave','RightSlave']
	#~ for i in [0,1]:
		#~ bMD.write('\toverInlet' + descList[i] + ' \n\t{ \n')
		#~ bMD.write('\ttype patch; \n')
		#~ bMD.write('\tfaces \n \t(\n')
		#~ bMD.write('\t( ' 												#inlet - top part sides
					#~ + 
					#~ repr(labls[-(4-i)][1]) + ' ' + repr(labls[-(2-i)][1]) 
					#~ + 
					#~ ' '
					#~ + 
					#~ repr(labls[-(2-i)][2]) + ' ' + repr(labls[-(4-i)][2]) 
					#~ + 
					#~ ' ) \n'
					#~ )
		#~ bMD.write('\t( ' 												#inlet - tip sides
					#~ + 
					#~ repr(labls[-(2-i)][-2]) + ' ' + repr(labls[3][4]) 
					#~ + 
					#~ ' '
					#~ + 
					#~ repr(labls[3][7]) + ' ' + repr(labls[-(2-i)][-1]) 
					#~ + 
					#~ ' ) \n'
					#~ )
		#~ bMD.write('\t);\n\t} \n\n')
		#~ bMD.write('\toverInlet' + descList[i+2] + ' \n\t{ \n')
		#~ bMD.write('\ttype patch; \n')
		#~ bMD.write('\tfaces \n \t(\n')
		#~ bMD.write('\t( ' 												#inlet - top part sides
					#~ + 
					#~ repr(labls[-(4-i)][1]) + ' ' + repr(labls[3][4]) 
					#~ + 
					#~ ' '
					#~ + 
					#~ repr(labls[3][7]) + ' ' + repr(labls[-(4-i)][2]) 
					#~ + 
					#~ ' ) \n'
					#~ )
		#~ bMD.write('\t);\n\t} \n\n')
	descList = ['Master','Slave']
	bMD.write('\toverInlet' + descList[0] + ' \n\t{ \n')
	bMD.write('\ttype patch; \n')
	bMD.write('\tfaces \n \t(\n')
	for j in [0,1]:
		bMD.write('\t( ' 												#inlet - top part sides
					+ 
					repr(labls[-(4-j)][1]) + ' ' + repr(labls[-(2-j)][1]) 
					+ 
					' '
					+ 
					repr(labls[-(2-j)][2]) + ' ' + repr(labls[-(4-j)][2]) 
					+ 
					' ) \n'
					)
		bMD.write('\t( ' 												#inlet - tip sides
					+ 
					repr(labls[-(2-j)][-2]) + ' ' + repr(labls[3][4]) 
					+ 
					' '
					+ 
					repr(labls[3][7]) + ' ' + repr(labls[-(2-j)][-1]) 
					+ 
					' ) \n'
					)
	bMD.write('\t);\n\t} \n\n')
	bMD.write('\toverInlet' + descList[1] + ' \n\t{ \n')
	bMD.write('\ttype patch; \n')
	bMD.write('\tfaces \n \t(\n')
	for j in [0,1]:
		bMD.write('\t( ' 												#inlet - top part sides
					+ 
					repr(labls[-(4-j)][1]) + ' ' + repr(labls[3][4]) 
					+ 
					' '
					+ 
					repr(labls[3][7]) + ' ' + repr(labls[-(4-j)][2]) 
					+ 
					' ) \n'
					)
	bMD.write('\t);\n\t} \n\n')	
	bMD.write('); \n\n')
	
	#-------------------------------------------------------------------
	# write mergePatchPairs
	bMD.write('mergePatchPairs \n( \n')
	bMD.write('\t (leftMaster leftSlave) \n')
	bMD.write('\t (rightMaster rightSlave) \n')
	bMD.write('\t (inletMaster inletSlave) \n')
	#~ bMD.write('\t (overInletMaster overInletSlave) \n')
	bMD.write('); \n\n')
	
	#-------------------------------------------------------------------
	# footline
	bMD.write('// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * // \n\n')
	
	#-------------------------------------------------------------------
	# close file
	bMD.close()

	return;
