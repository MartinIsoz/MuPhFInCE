#!/usr/bin/python

#FILE DESCRIPTION=======================================================
#~ Simple python function to enable some parametrization of the mesh
#~ created for the case of rivulet flow down an inclined plate
#~
#INPUTS-----------------------------------------------------------------
    #~ caseDir ...     path to directory with case data
    #~ a0      ...     initial rivulet width (inlet width)
    #~ h0      ...     initial rivulet height (inlet height)
    #~ cellW   ...     experimental cell width (m)
    #~ cellL   ...     experimental cell height
    #~ nCellsW ...     number of cells in cylinder width direction
    #~ nCellsL ...     number of cells in cylinder asimuthal direction
    #~ mScale  ...     scale of geometry in meters
#OUTPUTS----------------------------------------------------------------
    #~ blockMeshDict   ... dictionary for blockMesh application of oF

#LICENSE================================================================
#  blockMeshGenCyl.py
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
def fblockMeshGen(caseDir,
        a0=0.01,h0=0.001,
        cellW=0.150,cellL=0.300,
        nCellsW=150,nCellsL=300,
        mScale=1):

    #IMPORT BLOCK===========================================================
    import os
    import math
    #
    #GET THE DATA===========================================================
    #=======================================================================
    #                           EDITABLE
    #=======================================================================
    #-----------------------------------------------------------------------
    # GEOMETRY DATA
    #-----------------------------------------------------------------------
    # geometry arguments (all in [m])
    #~ a0   = 0.001                                                            #inlet width
    #~ h0   = 0.001								                            #initial rivulet height
    hG   = 0.01                                                               #geometry height (not important)
    #~ eps  = 0.01                                                             #h0/R
    #-----------------------------------------------------------------------
    # MESH DATA
    #-----------------------------------------------------------------------
    # number of cells in each direction for each part of the mesh
    nCellsH  = 1    #number of cells in height direction			!! DO NOT EDIT !!
    #~ nCellsW  = 180   #number of cells in width direction			!! ONLY EVEN NUMBER !!
    #~ nCellsL  = 140  #number of cells in length direction
    #
    #-----------------------------------------------------------------------
    # mesh grading
    grDX, grDY, grDZ = 1.0, 1.0, 1.0                                        #grading in dense block
    grSX, grSY, grSZ = 1.0, 1.0, 1.0                                        #gradins in sparse block
    
    # scale (to meters)
    #~ mScale = 1
    
    #=======================================================================
    #                           DO NOT EDIT
    #=======================================================================
    
    # recalculation for ND mesh - lenght is ND by inlet height
    L             = 1#h0
    a0,h0,cellW,cellL,hG = a0/L,h0/L,cellW/L,cellL/L,hG/L
    
    # auxiliary variables - geometry
    addVecL = [    0,    cellL]						                    #vertices on plate top and bottom
    addVecW = [-cellW/2,-a0/2,a0/2,cellW/2]			                #4 different levels in width direction
    addVecH = [    0,    hG]                                            #cell top and bottom
    
    # auxiliary variables - meshing
    nCellsIn   = int(round(a0/cellW*nCellsW)+round(a0/cellW*nCellsW)%2+1)
    nCellsWVec = [(nCellsW-nCellsIn)/2,nCellsIn,(nCellsW-nCellsIn)/2-1]
    
    # define matrix of vertices
    vert = []
    for W in addVecW:
        for H in addVecH:
            for L in addVecL:
                vert.append(([L,W,H]))
        
    # define labels for vertices and arcs
    lablsV = []
    numVL  = len(addVecH)*len(addVecL)                                  #number of vertices in layer
    for i in range(len(addVecW)):
        lablsV.append(list(range(0+i*numVL,numVL+i*numVL,1)))
        
    for row in lablsV:
        print row
    
    #=======================================================================
    #CREATE FILE AND WRITE THE DATA IN======================================
    bMD = open(caseDir + './constant/polyMesh/blockMeshDict','w')       #open file for writing
    
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
    
    #-----------------------------------------------------------------------
    # convert to metres
    bMD.write('convertToMeters \t' + repr(mScale) + '; \n\n')
    
    #-----------------------------------------------------------------------
    # write vertices
    bMD.write('vertices \n( \n')
    k = 0
    for row in vert:
        bMD.write('\t ( ' + ' '.join(str(e) for e in row) + ' )\t//' + repr(k) + '\n')
        k = k+1
    bMD.write('); \n\n')
    
    # write edges
    bMD.write('edges \n( \n')
    bMD.write('); \n\n')
    
    # write blocks
    auxList = range(len(lablsV)-1)
    bMD.write('blocks \n( \n')
    for i in auxList:
         bMD.write('\t hex \n')
         bMD.write('\t \t ( '
                        +
                        ' '.join(str(e) for e in lablsV[i][:2:1])
                        +
                        ' '
                        +
                        ' '.join(str(e) for e in lablsV[i+1][1::-1])
                        +
                        ' '
                        +
                        ' '.join(str(e) for e in lablsV[i][2::1])
                        +
                        ' '
                        +
                        ' '.join(str(e) for e in lablsV[i+1][:1:-1])
                        +
                        ' ) \n'
                        )
         bMD.write('\t \t ( ' + repr(nCellsL) + ' ' + repr(nCellsWVec[i]) + ' ' + repr(nCellsH) + ' ) ')
         bMD.write('\t simpleGrading ')
         bMD.write('\t ( ' + repr(1.0) + ' ' + repr(1.0) + ' ' + repr(1.0) + ' ) \n')
    bMD.write('); \n\n')
    
    # write boundaries
    bMD.write('boundary \n( \n')
    # -- inlet
    inLev   = int(math.floor(len(auxList)/2))
    lenLen  = int(math.floor(len(addVecL)/2))
    bMD.write('\tinlet \n\t{ \n')
    bMD.write('\ttype patch; \n')
    bMD.write('\tfaces \n \t(\n')
    bMD.write('\t \t ( '
                   +
                   ' '.join(str(e) for e in [lablsV[inLev][j] for j in [0,lenLen+1]])           #'4 6 10 8'
                   +
                   ' '
                   +
                   ' '.join(str(e) for e in [lablsV[inLev+1][j] for j in [lenLen+1,0]])
                   +
                   ' )\n'
                   )
    bMD.write('\t);\n\t} \n\n')
    # -- outlet
    bMD.write('\toutlet \n\t{ \n')
    bMD.write('\ttype patch; \n')
    bMD.write('\tfaces \n \t(\n')
    for i in range(len(auxList)):
        bMD.write('\t \t ( '
                        +
                        ' '.join(str(e) for e in [lablsV[i][j] for j in [lenLen,2*lenLen+1]])
                        +
                        ' '
                        +
                        ' '.join(str(e) for e in [lablsV[i+1][j] for j in [2*lenLen+1,lenLen]])
                        +
                        ' )\n'
                        )
    bMD.write('\t);\n\t} \n\n')
    # -- filmWalls
    bMD.write('\tfilmWalls \n\t{ \n')
    bMD.write('\ttype wall; \n')
    bMD.write('\tfaces \n \t(\n')
    for i in range(len(auxList)):
        bMD.write('\t \t ( '
                        +
                        ' '.join(str(e) for e in [lablsV[i][j] for j in [0,lenLen]])
                        +
                        ' '
                        +
                        ' '.join(str(e) for e in [lablsV[i+1][j] for j in [lenLen,0]])
                        +
                        ' )\n'
                        )
    bMD.write('\t);\n\t} \n\n')
    # -- sides -- not at all clean coding
    bMD.write('\tsides \n\t{ \n')
    bMD.write('\ttype patch; \n')
    bMD.write('\tfaces \n \t(\n')
    for i in [0,len(auxList)]:# sides - those should be really walls
        bMD.write('\t \t ( '
                        +
                        ' '.join(str(e) for e in [lablsV[i][j] for j in [0,lenLen]])
                        +
                        ' '
                        +
                        ' '.join(str(e) for e in [lablsV[i][j] for j in [2*lenLen+1,lenLen+1]])
                        +
                        ' )\n'
                        )
    for i in range(len(auxList)):#top - around the inlet, ?walls?
        if i != inLev:#skip the inlet
            bMD.write('\t \t ( '
                            +
                   ' '.join(str(e) for e in [lablsV[i][j] for j in [0,lenLen+1]])           #'4 6 10 8'
                   +
                   ' '
                   +
                   ' '.join(str(e) for e in [lablsV[i+1][j] for j in [lenLen+1,0]])
                   +
                            ' )\n'
                            )
    for i in range(len(auxList)):#top side - may be create an atmosphere?
        bMD.write('\t \t ( '
                        +
                        ' '.join(str(e) for e in [lablsV[i][j] for j in [lenLen+1,2*lenLen+1]])
                        +
                        ' '
                        +
                        ' '.join(str(e) for e in [lablsV[i+1][j] for j in [2*lenLen+1,lenLen+1]])
                        +
                        ' )\n'
                        )
    bMD.write('\t);\n\t} \n\n')
    bMD.write('); \n\n')
    
    bMD.write('mergePatchPairs \n( \n')
    bMD.write('); \n\n')
    
    #-----------------------------------------------------------------------
    # footline
    bMD.write('// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * // \n\n')
    
    #-----------------------------------------------------------------------
    # close file
    bMD.close()
    
    return;
    
