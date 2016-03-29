#!/usr/bin/python

#FILE DESCRIPTION=======================================================
#~ Python script used for post-processing automatization of the rivulet
#~ flow down the experimental plate in Freiberg
 
#~ PROGRAM STRUCTURE:
#~ 1.  Identify problems in data (caused by parazite currents)
    #~ - find yCoordMax and zCoordMax
#~ 2.  Remove the problems
    #~ - create isosurface int2Store (prepared gas-liquid interface)
#~ 3.  Prepare output variables
    #~ - Sgl, area of the gas liquid interface
        #~ - IntegrateVariables filter on int2Store, Cell Data
    #~ - aLaRVec, rivulet width (on l level) (aL + aR)
        #~ - Slice filter on int2Store, z = l + calculator, abs(coordsY)
        #~ - data minning and further manipulation (sum in tuples)
    #~ - h0Vec, rivulet height at centerline (y = 0)
        #~ - Slice filter on int2Store, y = 0
        #~ - data minning, no further manipulation needed
    #~ - epsVec = h0Vec./aVec (there should be the same number of elements)
    #~ NOTE: Same manipulations as for aVec and h0Vec were already
          #~ performed during the data problems identification

#~ NOTES:
    #~ - before running, the main file has to be highlighted
    #~ - can be ran from command line 
    #~ - still unfinished BUT improvement
    #~ - colors the rivulet by its hFun (same as in exp Data)
    #~ - coloring, <0,1.93> mm (corresponds to calibration cell)
    
#~ USAGE:
   #~ paraFoam --script=./rivuletPostProcSaveData.py

#~ OUTPUT:
    #~ modified row in iF_scalDataFile
        #~ ... to the appropriate row od the above specified file, append
            #~ Sgl, ReM
    #~ postProcVecs_iF_caseSpec
        #~ ... file containing the vector outputs that I am interested in
            #~ aLaRVec,h0Vec,epsVec,betaLVec,betaRVec
    #~ File content and structure:
        #~ Q0 = NUM (in m3/s)
        #~ Sgl = NUM (in m2)
        #~ !!ReM = NUM (in 1)!! (NOT YET IMPLEMENTED)
        #~ aLaRVec = [[x0,aL0 + aR0],...,[xN,aLN + aRN]]
        #~ h0Vec = [[x0,h00],...,[xN,h0N]]
        #~ epsVec = [[x0,eps0],...,[xN,epsN]]
        #~ betaVec = [[x0,beta0],...,[xN,beta]]
        #~ ---------------------------------------------------------
        #~ Q0      ... liquid volumetric flow rate
        #~ Sgl     ... rivulet gas-liquid interface area
        #~ ReM     ... maximal liquid Reynolds number in rivulet
        #~ aLaRVec ... width of the rivulet at z = l
        #~ h0Vec   ... height of the rivulet at y = 0
        #~ epsVec  ... ratio of rivulet height to its width (thin film approx)
        #~ betaVec ... dynamic contact angles at y = a (smoothed)

#LICENSE================================================================
#  rivuletProstProcSaveData.py
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

#=======================================================================
# PARAMETERS
xAll = 0.025                                                            #relative xCoord of case description
ySkip= 0.07                                                             #relative yCoord diff between 2 texts
lWet = 3e-5                                                             #"wetting level, m"
cellMax = 1.93e-3                                                       #maximal film thickness in cal. cell
xEOmit = 3e-3                                                           #distance from the plate end to omit in aVec, hVec, epsVec and betaL/RVec calculations
# -- folder for saving the output data
outDataFolder = "../05_PlateDCases/20_evPrep/10_postProcOutputs/"
# -- file for saving the scalar outputs
scalDataFile  = "iF_scalDataFile"

#=======================================================================
# IMPORT BLOCK
#~ try: paraview.simple
#~ except: from paraview.simple import *
import math
import glob
import os
# csv files handling
import sys
import csv
import operator
# function data smoothing (betaVec)
from scipy.interpolate import splrep,splev
import numpy as np

#=======================================================================
# FUNCTIONS DEFINITIONS
# FUNCTION TO EXTRACT DATA FROM PARAVIEW SOURCE
def fExtractVec(source2Write,dataType,sortColName,intColsNames):
    # function will go through the source2Write paraview source, sort it
    # in accordance to sortCol and return sortCol as list and intCols as
    # list of lists
    #
    # INPUTS:
    #   source2Write    ... paraview source
    #   dataType        ... what to write, can be "Points" or "Cells"
    #   sortColName     ... name of the column to sort the data
    #   intColsNames    ... name of the columns that I am interested in
    #
    # OUTPUTS:
    #   outs            ... list with sortCol as 1st element and intCols
    #                       as rest of the values
    #
    # NOTE: The function creates a temporary csv file
    fileNm   = "./tempFile.csv"
    
    dataWriter = CreateWriter(fileNm,source2Write)                           #create writer object
    dataWriter.FieldAssociation = "Points" # or "Cells"
    dataWriter.UpdatePipeline()
    
    del dataWriter
    
    # -- modify the resulting csv file (standard python)
    # Note: 1. I need to sort the data by x-coordinate (column end-2)
    #       2. I need to add always 2 values of aFunRes
    
    
    with open("tempFile0.csv","rb") as csvfile:
        reader = csv.reader(csvfile, delimiter=",")
        colTitles = reader.next()                                       #save column names
        sortCol   = colTitles.index(sortColName)                        #I want to sort by sortColName
        intCols   = [colTitles.index(cNm) for cNm in intColsNames]      #get positions of data that I am interested in
        
        prepList  = []                                                      #read the data
        for row in reader:
            prepList.append(row)
            
    redList = [row for row in prepList if 1e3*float(row[sortCol]) % 1 == 0] #data every mm (!! MESH SIZE !!)
    
    # sort columns of the list
    sortedList = sorted(redList, key=operator.itemgetter(sortCol), reverse=False)
    
    # get the informations that I am interested in
    outCols= [sortCol]                                                  #create list of indexes that I want to return (initiate with independent variable)
    outCols= [outCols.append(cInd) for cInd in intCols]                 #append the indexes of the colums that I am interested in
    outs   = [[row[sortCol] for row in sortedList]]                     #initiate outs by putting in the column of independet variable
    for col in intCols:                                                 #add the columns I am interested in
        outs.append([row[col] for row in sortedList])
    
    os.remove("tempFile0.csv")                                          #remove the temporary file
    
    return outs                                                         #return the result
    
#=======================================================================
# POSTPROCESSING INITIATION
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

activeSource_OpenFOAM = FindSource( mainCase[0][2::] )                  #remove ./ from the name

# GO TO THE ANIMATION (TIME RANGE) END==================================
AnimationScene1 = GetAnimationScene()
AnimationScene1.GoToLast()

Render()

# CREATE A SCALAR CLIP - STORE ONLY THE RIVULET=========================
liqOnly = Clip( ClipType="Scalar", guiName="liqOnly" )

liqOnly.Scalars = ['POINTS', 'alpha.liquid']
liqOnly.Value = 0.5                                                     #alpha.liquid >= 0.5

liqOnlyRepresentation = Show()

liqOnlyRepresentation.Opacity = 1.0
liqOnlyRepresentation.Visibility = 0

#~ Render()

#=======================================================================
# A - FINDING THE PROPER INTERFACE (INT2STORE)
# OUTLIERS FINDING======================================================
# CREATE AN ISOSURFACE - SHOW ONLY THE INTERFACE========================
SetActiveSource(FindSource( mainCase[0][2::] ))                         #remove ./ from the name
# -- use isosurface
intOnly = Contour( PointMergeMethod="Uniform Binning", guiName="intOnly" )

intOnly.ContourBy  = ['POINTS', 'alpha.liquid']
intOnly.Isosurfaces = [0.501]                                             #alpha.liquid = 0.5

intOnlyRepresentation = Show()

intOnlyRepresentation.Opacity = 1.0
intOnlyRepresentation.Visibility = 0

#~ Render()

# 1. PROPER SCALING FOR ZCOORD
# CREATE A CLIP AT Z=0 - CORRECT HFUN SCALING===========================
zBaseLineRiv = Clip( ClipType="Plane", guiName="zBaseLineRiv")

zBaseLineRiv.ClipType.Origin = [0.0, 0.0, 0.0]
zBaseLineRiv.ClipType.Normal = [0.0, 0.0, 1.0]

zBaseLineRivRepresentation = Show()
zBaseLineRivRepresentation.Visibility = 0

#~ Render()

# CREATE A SLICE AZ Y=0 - CORRECT HFUN SCALING==========================
yBaseLineRiv = Slice( SliceType="Plane", guiName="yBaseLineRiv")

yBaseLineRiv.SliceOffsetValues = [0.0]
yBaseLineRiv.SliceType.Origin = [0.0, 0.0, 0.0]
yBaseLineRiv.SliceType.Normal = [0.0, 1.0, 0.0]

yBaseLineRivRepresentation = Show()
yBaseLineRivRepresentation.Visibility = 0

#~ Render()

# CREATE A CALCULATOR TO GET THE HFUN===================================
hFunScale     = Calculator( guiName="hFunScale" )

hFunScale.Function = 'coordsZ'
hFunScale.ResultArrayName = 'hFun'

hFunScaleRepresentation = Show()
hFunScaleRepresentation.Visibility = 0

#~ Render()

# CALCULATE THE DESCRIPTIVE STATISTIC (I WANT PROPER SCALING)===========
descStatsZ   = DescriptiveStatistics(guiName="descStatsZ")

descStatsZ.AttributeMode = 'Point Data'
descStatsZ.VariablesofInterest = ['hFun']
descStatsZ.TrainingFraction    = 0.5                                     #use 50% of the available data

sData = servermanager.Fetch(descStatsZ)

RowData = sData.GetBlock(0).GetBlock(0).GetBlock(0).GetRowData()        #there must be a more direct approach

meanMaxH= RowData.GetArray(4).GetValue(0)                               #mean of riv. height at centerline
sigMaxH = RowData.GetArray(5).GetValue(0)                               #std. dev of riv. height at centerline
zCoordMax  = meanMaxH + 30*3*sigMaxH

#~ Render()
#~ 
# 2. PROPER SCALING FOR YCOORD
# CREATE A SLICE AT Z=l (3E-5 M)========================================
SetActiveSource(intOnly)                                                #work on the interface
plateLevel = Slice( SliceType="Plane", guiName="plateLevel")

plateLevel.SliceOffsetValues = [0.0]
plateLevel.SliceType.Origin = [0.0, 0.0, lWet]
plateLevel.SliceType.Normal = [0.0, 0.0, 1.0]

plateLevelRepresentation = Show()
plateLevelRepresentation.Visibility = 0

#~ Render()

# GET YCOORDS (RIVULET WIDTHS) AT THE SLICE=============================
aFunRivPlateLev   = Calculator( guiName="aFunRivPlateLev" )

aFunRivPlateLev.Function = 'abs(coordsY)'
aFunRivPlateLev.ResultArrayName = 'aFunPlateLev'

aFunRivPlateLevRepresentation = Show()
aFunRivPlateLevRepresentation.Visibility = 0

#~ Render()

# GET THE RIVULET WIDTH AT HALF OF THE PLATE============================
# -- get plate length (xMax)
allData = servermanager.Fetch(activeSource_OpenFOAM)
xMax    = allData.GetBlock(0).GetBlock(0).GetBounds()
xMax    = xMax[1]                                                       #(xMin,xMax,yMin,yMax,zMin,zMax)
xHalf   = xMax/2                                                        #half of the plate
# -- use slice at x=xHalf (should be only 2 points)
SetActiveSource(aFunRivPlateLev)
aHalfRiv   = Slice( SliceType="Plane", guiName="aHalfRiv")

aHalfRiv.SliceOffsetValues = [0.0]
aHalfRiv.SliceType.Origin = [xHalf, 0.0, 0.0]
aHalfRiv.SliceType.Normal = [1.0, 0.0, 0.0]

aHalfRivRepresentation = Show()
aHalfRivRepresentation.Visibility = 0

#~ Render()

# -- get values from the container (again, quite ugly way)
aHalfData = servermanager.Fetch(aHalfRiv)                                     #fetch the variable
aHalfData = aHalfData.GetBlock(0).GetBlock(0)                                 #extract vtkPolyData
aHalfData = aHalfData.GetPointData().GetArray(4)                              #get yCoords/aFun (vtkArray)

nVals  = aHalfData.GetNumberOfTuples()                                     #should be 2, but better safe then sorry

aHalfVals = []
for i in range(nVals):
    aHalfVals.append(aHalfData.GetTuple1(i))                                  #store the data

aHalfAvg  = sum(aHalfVals)/nVals                                              #calculate mean value

# PREPARE A THIN STRIPE OF DATA FOR DADX(XHALF) CALCULATION=============
SetActiveSource(aFunRivPlateLev)                                        #work with aFun at plate level
# -- prepare the top clip
aFunRivPlatePartTop = Clip( ClipType="Plane", guiName="aFunRivPlatePartTop")

aFunRivPlatePartTop.ClipType.Origin = [xHalf-5e-3, 0.0, 0.0]
aFunRivPlatePartTop.ClipType.Normal = [1.0, 0.0, 0.0]

aFunRivPlatePartTopRepresentation = Show()
aFunRivPlatePartTopRepresentation.Visibility = 0
Render()
# -- prepare the bottom clip
aFunRivPlatePartBot = Clip( ClipType="Plane", guiName="aFunRivPlatePartBot")

aFunRivPlatePartBot.ClipType.Origin = [xHalf+5e-3, 0.0, 0.0]
aFunRivPlatePartBot.ClipType.Normal = [-1.0, 0.0, 0.0]

aFunRivPlatePartBotRepresentation = Show()
aFunRivPlatePartBotRepresentation.Visibility = 0

#~ Render()

# CALCULATE GRADIET OF AFUN=============================================
aFunRivPlateLevGrad  = GradientOfUnstructuredDataSet( guiName="aFunRivPlateLevGrad" )

aFunRivPlateLevGrad.ScalarArray     = ['POINTS','aFunPlateLev']
aFunRivPlateLevGrad.ResultArrayName = 'aFunPlateLevGrad'

aFunRivPlateLevGradRepresentation = Show()
aFunRivPlateLevGradRepresentation.Visibility = 0

#~ Render()

# CALCULATE ABSOLUTE VALUE OF DADY======================================
dadxABS     = Calculator( guiName="dadxABS" )

dadxABS.Function = 'abs(aFunPlateLevGrad_X)'
dadxABS.ResultArrayName = 'dadxABS'

dadxABSRepresentation = Show()
dadxABSRepresentation.Visibility = 0

#~ Render()

# REMOVE ALL THE VALUES >= k (UNPHYSICAL)===============================
dadxABSle1  = Clip( ClipType="Scalar", guiName="dadxABSle1" )

dadxABSle1.Scalars = ['POINTS', 'dadxABS']
dadxABSle1.Value = 0.1                                                  #abs(DaDx) <= 0.1
dadxABSle1.InsideOut = 1

dadxABSle1Representation = Show()

dadxABSle1Representation.Opacity = 1.0
dadxABSle1Representation.Visibility = 0

#~ Render()

# CALCULATE DESCRIPTIVE STATISTICS ON THE REST==========================
descStatsY   = DescriptiveStatistics(guiName="descStatsY")

descStatsY.AttributeMode = 'Point Data'
descStatsY.VariablesofInterest = ['dadxABS']
descStatsY.TrainingFraction    = 1.0                                     #use 50% of the available data

sData = servermanager.Fetch(descStatsY)

RowData = sData.GetBlock(0).GetBlock(0).GetBlock(0).GetRowData()        #there must be a more direct approach

meanDaDx= RowData.GetArray(4).GetValue(0)                               #mean of riv. height at centerline
sigDaDx = RowData.GetArray(5).GetValue(0)                               #std. dev of riv. height at centerline
dadxMax  = meanDaDx + 3*sigDaDx

#~ Render()

# CALCULATE MAXIMAL RIVULET WIDTH=======================================
# -- estimate based on a first degree taylor polynomial
yCoordMax= aHalfAvg + dadxMax*xHalf

#=======================================================================
# OUTLIERS REMOVAL======================================================
# 1. TO HIGH VALUES OF ZCOORD (AND PREPARATION FOR PROPER COLORING)
# ADDRESS HFUN FIELD TO THE RIVULET (LIQONLY)===========================
SetActiveSource(liqOnly)                                                #I will work with this source
hFunRiv     = Calculator( guiName="hFunRiv" )

hFunRiv.Function = 'coordsZ'
hFunRiv.ResultArrayName = 'hFun'

hFunRivRepresentation = Show()
hFunRivRepresentation.Visibility = 0

#~ Render()

# REMOVE OUTLIERS (IN Z-DIRECTION)======================================
rivWOZOut   = Clip( ClipType="Scalar", guiName="rivWOZOut" )

rivWOZOut.Scalars   = ['POINTS', 'hFun']
rivWOZOut.Value     = zCoordMax                                            #hFun <= zCoordMax
rivWOZOut.InsideOut = 1

rivWOZOutRepresentation = Show()

rivWOZOutRepresentation.Opacity = 1.0
rivWOZOutRepresentation.Visibility = 0

#~ Render()

# 2. TO HIGH VALUES OF ABS(YCOORD)
# ADDRESS HFUN FIELD TO THE RIVULET (LIQONLY)===========================
aFunRiv     = Calculator( guiName="aFunRiv" )

aFunRiv.Function = 'abs(coordsY)'
aFunRiv.ResultArrayName = 'aFun'

aFunRivRepresentation = Show()
aFunRivRepresentation.Visibility = 0

#~ Render()
# REMOVE OUTLIERS (IN Y-DIRECTION)======================================
rivWOAOut   = Clip( ClipType="Scalar", guiName="rivWOAOut" )

rivWOAOut.Scalars   = ['POINTS', 'aFun']
rivWOAOut.Value     = yCoordMax                                          #aFun <= yCoordMax
rivWOAOut.InsideOut = 1

rivWOAOutRepresentation = Show()

rivWOAOutRepresentation.Opacity = 1.0
rivWOAOutRepresentation.Visibility = 0

#~ Render()

# GET THE INTERFACE WITHOUT OUTLIERS====================================
# -- use isosurface
intOnlyWAOoutL = Contour( PointMergeMethod="Uniform Binning", guiName="intOnlyWAOoutL" )

intOnlyWAOoutL.ContourBy  = ['POINTS', 'alpha.liquid']
intOnlyWAOoutL.Isosurfaces = [0.501]                                             #alpha.liquid = 0.5

intOnlyWAOoutLRepresentation = Show()

intOnlyWAOoutLRepresentation.Opacity = 1.0
intOnlyWAOoutLRepresentation.Visibility = 0

#~ Render()

# STORE ONLY THE PART WHERE X>=0========================================
int2Store = Clip( ClipType="Plane", guiName="int2Store" )

int2Store.ClipType.Origin = [0.0, 0.0, 0.0]
int2Store.ClipType.Normal = [1.0, 0.0, 0.0]

int2StoreRepresentation = Show()
int2StoreRepresentation.Visibility = 1
Render()

# WRITE DATA TO CSV FILE================================================
# -- only current (last) time step
# -- only the interface (for MATLAB interface size calculation)

cTime   = float("%s"%AnimationScene1.GetProperty('AnimationTime'))      #get current time

fileNm   = ( 
            "./matlabDATA/GLI_"
            +
            "%s"%AnimationScene1.GetProperty('AnimationTime')
            +
            "s.csv"
          )

source2Write = int2Store                                                #set which source to write to data

dataWriter = CreateWriter(fileNm,source2Write)                           #create writer object
dataWriter.FieldAssociation = "Points" # or "Cells"
dataWriter.UpdatePipeline()

del dataWriter

#=======================================================================
# B - PREPARING THE OUTPUT VARIABLES (AVEC,H0VEC,SGL...)
# CALCULATE SGL (AREA IF GAS-LIQUID INTERFACE)==========================
# Note: will calculate Sgl and save it as appropriately named empty file
SetActiveSource( int2Store )                                            #ensure proper active source

integrateVars = IntegrateVariables( guiName = "integrateVars")          #create the filter

Sgl = integrateVars.GetCellDataInformation().GetArray('Area').GetRange(0)#dig out data
Sgl = Sgl[0]                                                            #command above returns tupple

# -- clear previous results
fl2Rem  = glob.glob("Sgl_*")                                            #get list of all the stored results
for fileNm in fl2Rem:
    os.remove(fileNm)                                                   #remove all the previous results

SglFile = open("Sgl_%.6f_m2"%Sgl,'w')                                   #write the result as a text file

SglFile.close()

# CALCULATE ALARVEC (WIDTH OF THE RIVULET AT LWET LEVEL)================
SetActiveSource( int2Store )                                            #ensure proper active source

# -- create filter (slice) at z = lWet (get only lWet level of interface)
int2StorePlateLevel = Slice( SliceType="Plane", guiName="int2StorePlateLevel")

int2StorePlateLevel.SliceOffsetValues = [0.0]
int2StorePlateLevel.SliceType.Origin = [0.0, 0.0, lWet]
int2StorePlateLevel.SliceType.Normal = [0.0, 0.0, 1.0]
int2StorePlateLevel.Triangulatetheslice = 0

int2StorePlateLevelRepresentation = Show()
int2StorePlateLevelRepresentation.Visibility = 0
#~ Render()

# -- create filter (clip) at x = L-xEOmit mm (get rid of the plate end)
int2StorePlateLevelMOD = Clip ( ClipType="Plane", guiName="int2StorePlateLevelMOD")

int2StorePlateLevelMOD.ClipType.Origin = [xMax-xEOmit, 0.0, 0.0]
int2StorePlateLevelMOD.ClipType.Normal = [-1.0, 0.0, 0.0]

int2StorePlateLevelMODRepresentation = Show()
int2StorePlateLevelMODRepresentation.Visibility = 0

# -- calculate rivulet half widths
aFunRivRes   = Calculator( guiName="aFunRivRes" )

aFunRivRes.Function = 'abs(coordsY)'
aFunRivRes.ResultArrayName = 'aFunRes'

aFunRivResRepresentation = Show()
aFunRivResRepresentation.Visibility = 0

#~ Render()

#-----------------------------------------------------------------------
# Note: work with vtk poly anything is utterly painful =>
#       => save the desired data as temporary csv file, work with them
#          and reload them again after (the data are not that big)
# -- exported to a function (will be used multiple times)

xVecALARVec = fExtractVec(aFunRivRes,'Point Data','Points:0',['aFunRes'])
#-----------------------------------------------------------------------


# CALCULATE H0VEC (HEIGHT OF THE RIVULET AT CENTERLINE)=================
SetActiveSource( int2Store )                                            #ensure proper active source

# -- create filter (slice) at y = 0 (get only interface at centerline)
y0Int = Slice( SliceType="Plane", guiName="y0Int")

y0Int.SliceOffsetValues = [0.0]
y0Int.SliceType.Origin = [0.0, 0.0, 0.0]
y0Int.SliceType.Normal = [0.0, 1.0, 0.0]

y0IntRepresentation = Show()
y0IntRepresentation.Visibility = 0
Render()

# -- create filter (clip) at x = L-xEOmit mm (get rid of the plate end)
y0IntMOD = Clip ( ClipType="Plane", guiName="y0IntMOD")

y0IntMOD.ClipType.Origin = [xMax-xEOmit, 0.0, 0.0]
y0IntMOD.ClipType.Normal = [-1.0, 0.0, 0.0]

y0IntMODRepresentation = Show()
y0IntMODRepresentation.Visibility = 0

# -- calculate rivulet height
hFunRivResPREP     = Calculator( guiName="hFunRivResPREP" )

hFunRivResPREP.Function = 'coordsZ'
hFunRivResPREP.ResultArrayName = 'hFunRes'

hFunRivResPREPRepresentation = Show()
hFunRivResPREPRepresentation.Visibility = 0

#~ Render()

# -- remove height outliers
# NOTE: I need to store those data for better Sgl calculation, but now,
#       I can safely remove them
hFunRivRes   = Clip( ClipType="Scalar", guiName="hFunRivRes" )

hFunRivRes.Scalars   = ['POINTS', 'hFun']
hFunRivRes.Value     = meanMaxH + 3*3*sigMaxH                        #higher than it should be - waves
hFunRivRes.InsideOut = 1

hFunRivResRepresentation = Show()
hFunRivResRepresentation.Visibility = 0

#~ Render()

# -- extract the data and save it as h0Vec (rivulet height at centerline)
#-----------------------------------------------------------------------
# Note: work with vtk poly anything is utterly painful =>
#       => save the desired data as temporary csv file, work with them
#          and reload them again after (the data are not that big)
# -- exported to a function (will be used multiple times)

xVecH0Vec = fExtractVec(hFunRivRes,'Point Data','Points:0',['hFun'])

# CALCULATE EPSVEC (HEIGHT TO WIDTH RIVULET RATIO)======================
# Note: purely orientational results, obtained through various not so
#       bulletproof methods
nData     = min(len(xVecALARVec[0][::2]),len(xVecH0Vec[0]))             #get number of available data
xVec      = [float(s) for s in xVecH0Vec[0]]                            #independent variable
aLaRVec   = [float(x)+float(y) for (x,y) in zip(xVecALARVec[1][:-1:2],xVecALARVec[1][1::2])]#total rivulet width
# Note: I need to sum every 2 elements
h0Vec     = [float(s) for s in xVecH0Vec[1]]                            #rivulet height at y=0
# -- clip the lists to the same length (nData)
xVec,aLaRVec,h0Vec = xVec[:nData],aLaRVec[:nData],h0Vec[:nData]
# -- calculate rivulet height to width ratio
epsVec    = [h0Vec[i]/aLaRVec[i] for i in range(nData)]                 #rivulet height to width ratio


# CALCULATE BETA#VEC (RIVULET DYNAMIC CONTACT ANGLES====================
SetActiveSource( int2Store )                                            #ensure proper active source

# -- create filter (clip) for z >= lWet (above lWet level of interface)
int2StoreAboveLWet = Clip ( ClipType="Plane", guiName="int2StoreAboveLWet")

int2StoreAboveLWet.ClipType.Origin = [0.0, 0.0, 7*lWet]
int2StoreAboveLWet.ClipType.Normal = [0.0, 0.0, 1.0]

int2StoreAboveLWetRepresentation = Show()
int2StoreAboveLWetRepresentation.Visibility = 0

# -- create filter (clip) for z <= 0.1 mm (only rivulet edges)
int2StoreAboveLWet = Clip ( ClipType="Plane", guiName="int2StoreAboveLWet")

int2StoreAboveLWet.ClipType.Origin = [0.0, 0.0, 10*lWet]
int2StoreAboveLWet.ClipType.Normal = [0.0, 0.0, -1.0]

int2StoreAboveLWetRepresentation = Show()
int2StoreAboveLWetRepresentation.Visibility = 0

# -- calculate rivulet height
hFunRivBeta     = Calculator( guiName="hFunRivBeta" )

hFunRivBeta.Function = 'coordsZ'
hFunRivBeta.ResultArrayName = 'hFunBeta'

hFunRivBetaRepresentation = Show()
hFunRivBetaRepresentation.Visibility = 0

Render()

# -- calculate gradients (I need dhdy)
hFunRivBetaGrad  = GradientOfUnstructuredDataSet( guiName="hFunRivBetaGrad" )

hFunRivBetaGrad.ScalarArray     = ['POINTS','hFunBeta']
hFunRivBetaGrad.ResultArrayName = 'hFunBetaGrad'

hFunRivBetaGradRepresentation = Show()
hFunRivBetaGradRepresentation.Visibility = 0

Render()

# -- convert to absolute values and calculate atan (tan\beta = h')
absBetaRes     = Calculator( guiName="absBetaRes" )

absBetaRes.Function = 'atan(abs(hFunBetaGrad_Z))'
absBetaRes.ResultArrayName = 'absBetaRes'

absBetaResRepresentation = Show()
absBetaResRepresentation.Visibility = 0

Render()

# -- extract the data and save it as h0Vec (rivulet height at centerline)
#-----------------------------------------------------------------------
# Note: work with vtk poly anything is utterly painful =>
#       => save the desired data as temporary csv file, work with them
#          and reload them again after (the data are not that big)
# -- exported to a function (will be used multiple times)

xVecBetaVec = fExtractVec(absBetaRes,'Point Data','Points:0',['absBetaRes'])

# -- calculate means of measured values (for each distance from plate top)
betaVec   = []                                                          #dirty but working
auxVal    = float(xVecBetaVec[1][0])
for i in range(len(xVecBetaVec[0])-1):
    if xVecBetaVec[0][i] == xVecBetaVec[0][i+1]:
        auxVal = auxVal + float(xVecBetaVec[1][i+1])
    else:
        betaVec.append(auxVal)
        auxVal  = 0
        
# -- data smoothing (the cheating part)
xNpArray = np.array(xVec)                                               #save as np.array
yNpArray = np.array(betaVec)

xNpArray = xNpArray[:min(len(xNpArray),len(yNpArray))]                  #get rid of orphan points
yNpArray = yNpArray[:min(len(xNpArray),len(yNpArray))]

tckNpArray = splrep(xNpArray, yNpArray, w=None, xb=None, xe=None, k=3, task=0, s=0.03, t=None, full_output=0, per=0, quiet=1)

# Note: smoothing factor, s seems to be well arranged between 0.01 ans 0.05
#       (this is basically cheating)
betaVecSm = splev(xNpArray,tckNpArray,der=0,ext=0).tolist()             #get values of smoothed betaVec

#=======================================================================
# C - RESULTS STORING
# POSTPROCVECS_ FILES===================================================
vecsFileOut = [xVec,aLaRVec,h0Vec,epsVec,betaVec,betaVecSm]             #put output variables together
vecsFileOut = zip(*vecsFileOut)                                         #write by rows
for i in range(len(vecsFileOut)):                                       #convert to strings (writing)
    vecsFileOut[i] = list(vecsFileOut[i])                               #convert tuple to list
    for j in range(len(vecsFileOut[i])):
        vecsFileOut[i][j] = "%5.5e"%vecsFileOut[i][j]

colNames    = ['xVec','aLaRVec','h0Vec','epsVec','betaVec','betaVecSm'] #column names of the data

vecsFileOut.insert(0,colNames)                                          #insert column names to output data

outFile     = ('postProcVecs_' + mainCase[0][2::]).split('.OpenFOAM')[0]#output file name

with open(outDataFolder+outFile, 'w') as file:                          #write the data to the output file
    for row in vecsFileOut:
        for el in row:
            file.write(el+'\t')
        file.write('\n')
# IFSCALDATA FILE=======================================================
# Note: I need to find the right row and write (append) the results to it

caseIdentification = mainCase[0][2::].split('.OpenFOAM')[0].split('_') #split the case name file by data

solver,volFlow,plateIncl,liqName = caseIdentification

volFlow = "%5.4e"%float(volFlow)                                        #convert volumetric flow rate to right format

idStr = [liqName + '\t' + plateIncl + '\t' + volFlow]                   #line encoding

pVals = [
            "%5.4e"%Sgl,                                                #area of gas-liquid interface
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



#=======================================================================
# D - DATA DESCRIPTION AND GRAPHICAL OUTPUT (FOR CONTROL)
# SCALAR BAR============================================================
colorObjectRepresentation = int2StoreRepresentation                #what object will be colored

a0_hFun_PVLookupTable = GetLookupTableForArray( "hFun", 0,
    RGBPoints=[0.0, 0.0, 0.0, 0.0, cellMax, 1.0, 1.0, 1.0],
    ColorSpace='RGB',
    ScalarRangeInitialized=1.0 )

a0_hFun_PiecewiseFunction = CreatePiecewiseFunction( Points=[0.0, 0.0, 0.5, 0.0, 1.0, 1.0, 0.5, 0.0] )

colorObjectRepresentation.Representation = 'Surface'
colorObjectRepresentation.ColorArrayName = ('POINT_DATA', 'hFun')
colorObjectRepresentation.LookupTable = a0_hFun_PVLookupTable

a0_hFun_PVLookupTable.ScalarOpacityFunction = a0_hFun_PiecewiseFunction
        
Render()

ScalarBarWidgetRepresentation = CreateScalarBar( Title='$h(x,y),[\mathrm{m}]$',
 ComponentTitle='',
 LabelFontSize=12,
 Enabled=1,
 LookupTable=a0_hFun_PVLookupTable,
 TitleFontSize=14,
 LabelFormat='$%-#5.2e$')
RenderView1.Representations.append(ScalarBarWidgetRepresentation)

Render()

# ADD CASE TITLE========================================================
caseTitle = Text( guiName="caseTitle")

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
         
nu0     =	[1.11e-05, 1.55e-05]
gamma0  =	1.79e-02
rho0    =	[9.40e+02, 1.18e+00]
Q0      =	2.64e-06
alpha0  =	  60
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

#~ # try to rescale the colors for deltaf
#~ AnimationScene1 = GetAnimationScene()
#~ AnimationScene1.GoToLast()
#~ 
#~ Render()

# camera position

ResetCamera()
RenderView1 = GetRenderView()
RenderView1.CameraViewUp = [-0.8, -0.5, 0]
RenderView1.CameraFocalPoint = [0.15,-0.1,0]                               #center of the plate
RenderView1.CameraClippingRange = [5, 5]                                #who knows what it does...
RenderView1.CameraPosition = [0.2,0.15,0.2]

Render()

#=======================================================================    
# DATA STRUCTURES=======================================================
# NOTE: Get anything from DescriptiveStatistics filter seems rather complex
#-----------------------------------------------------------------------
# OUTPUT FROM sData = servermanager.Fetch(descStats)
#~ vtkMultiBlockDataSet (0x1da592c0)
  #~ Debug: Off
  #~ Modified Time: 964256
  #~ Reference Count: 1
  #~ Registered Events: (none)
  #~ Information: 0x1bd5d110
  #~ Data Released: False
  #~ Global Release Data: Off
  #~ UpdateTime: 0
  #~ Field Data:
    #~ Debug: Off
    #~ Modified Time: 964224
    #~ Reference Count: 1
    #~ Registered Events: (none)
    #~ Number Of Arrays: 0
    #~ Number Of Components: 0
    #~ Number Of Tuples: 0
  #~ Number Of Children: 1
  #~ Child 0: vtkMultiBlockDataSet
    #~ Debug: Off
    #~ Modified Time: 964251
    #~ Reference Count: 2
    #~ Registered Events: (none)
    #~ Information: 0x1bd5d560
    #~ Data Released: False
    #~ Global Release Data: Off
    #~ UpdateTime: 0
    #~ Field Data:
      #~ Debug: Off
      #~ Modified Time: 964231
      #~ Reference Count: 1
      #~ Registered Events: (none)
      #~ Number Of Arrays: 0
      #~ Number Of Components: 0
      #~ Number Of Tuples: 0
    #~ Number Of Children: 1
    #~ Child 0: vtkMultiBlockDataSet
      #~ Debug: Off
      #~ Modified Time: 964246
      #~ Reference Count: 2
      #~ Registered Events: (none)
      #~ Information: 0x1bd5d090
      #~ Data Released: False
      #~ Global Release Data: Off
      #~ UpdateTime: 0
      #~ Field Data:
        #~ Debug: Off
        #~ Modified Time: 964237
        #~ Reference Count: 1
        #~ Registered Events: (none)
        #~ Number Of Arrays: 0
        #~ Number Of Components: 0
        #~ Number Of Tuples: 0
      #~ Number Of Children: 2
      #~ Child 0: vtkTable
        #~ Debug: Off
        #~ Modified Time: 962786
        #~ Reference Count: 1
        #~ Registered Events: (none)
        #~ Information: 0x1bce3d80
        #~ Data Released: False
        #~ Global Release Data: Off
        #~ UpdateTime: 0
        #~ Field Data:
          #~ Debug: Off
          #~ Modified Time: 962767
          #~ Reference Count: 1
          #~ Registered Events: (none)
          #~ Number Of Arrays: 0
          #~ Number Of Components: 0
          #~ Number Of Tuples: 0
        #~ RowData: 
          #~ Debug: Off
          #~ Modified Time: 962785
          #~ Reference Count: 2
          #~ Registered Events: (none)
          #~ Number Of Arrays: 8
          #~ Array 0 name = Variable
          #~ Array 1 name = Cardinality
          #~ Array 2 name = Minimum
          #~ Array 3 name = Maximum
          #~ Array 4 name = Mean
          #~ Array 5 name = M2
          #~ Array 6 name = M3
          #~ Array 7 name = M4
          #~ Number Of Components: 8
          #~ Number Of Tuples: 1
          #~ Copy Tuple Flags: ( 1 1 1 1 1 0 1 1 )
          #~ Interpolate Flags: ( 1 1 1 1 1 0 0 1 )
          #~ Pass Through Flags: ( 1 1 1 1 1 1 1 1 )
          #~ Scalars: (none)
          #~ Vectors: (none)
          #~ Normals: (none)
          #~ TCoords: (none)
          #~ Tensors: (none)
          #~ GlobalIds: (none)
          #~ PedigreeIds: (none)
          #~ EdgeFlag: (none)
      #~ Child 1: vtkTable
        #~ Debug: Off
        #~ Modified Time: 962806
        #~ Reference Count: 1
        #~ Registered Events: (none)
        #~ Information: 0x1bce3650
        #~ Data Released: False
        #~ Global Release Data: Off
        #~ UpdateTime: 0
        #~ Field Data:
          #~ Debug: Off
          #~ Modified Time: 962790
          #~ Reference Count: 1
          #~ Registered Events: (none)
          #~ Number Of Arrays: 0
          #~ Number Of Components: 0
          #~ Number Of Tuples: 0
        #~ RowData: 
          #~ Debug: Off
          #~ Modified Time: 962805
          #~ Reference Count: 1
          #~ Registered Events: (none)
          #~ Number Of Arrays: 5
          #~ Array 0 name = Standard Deviation
          #~ Array 1 name = Variance
          #~ Array 2 name = Skewness
          #~ Array 3 name = Kurtosis
          #~ Array 4 name = Sum
          #~ Number Of Components: 5
          #~ Number Of Tuples: 1
          #~ Copy Tuple Flags: ( 1 1 1 1 1 0 1 1 )
          #~ Interpolate Flags: ( 1 1 1 1 1 0 0 1 )
          #~ Pass Through Flags: ( 1 1 1 1 1 1 1 1 )
          #~ Scalars: (none)
          #~ Vectors: (none)
          #~ Normals: (none)
          #~ TCoords: (none)
          #~ Tensors: (none)
          #~ GlobalIds: (none)
          #~ PedigreeIds: (none)
          #~ EdgeFlag: (none)
#-----------------------------------------------------------------------
# OUTPUT FROM RowData = sData.GetBlock(0).GetBlock(0).GetBlock(0).GetRowData()
#~ vtkDataSetAttributes (0x1bd4e430)
  #~ Debug: Off
  #~ Modified Time: 962785
  #~ Reference Count: 2
  #~ Registered Events: (none)
  #~ Number Of Arrays: 8
  #~ Array 0 name = Variable
  #~ Array 1 name = Cardinality
  #~ Array 2 name = Minimum
  #~ Array 3 name = Maximum
  #~ Array 4 name = Mean
  #~ Array 5 name = M2
  #~ Array 6 name = M3
  #~ Array 7 name = M4
  #~ Number Of Components: 8
  #~ Number Of Tuples: 1
  #~ Copy Tuple Flags: ( 1 1 1 1 1 0 1 1 )
  #~ Interpolate Flags: ( 1 1 1 1 1 0 0 1 )
  #~ Pass Through Flags: ( 1 1 1 1 1 1 1 1 )
  #~ Scalars: (none)
  #~ Vectors: (none)
  #~ Normals: (none)
  #~ TCoords: (none)
  #~ Tensors: (none)
  #~ GlobalIds: (none)
  #~ PedigreeIds: (none)
  #~ EdgeFlag: (none)
#-----------------------------------------------------------------------
# OUTPUT FROM a0Data = servermanager.Fetch(a0Riv)
#~ vtkMultiBlockDataSet (0x160fae0)
  #~ Debug: Off
  #~ Modified Time: 4084417
  #~ Reference Count: 1
  #~ Registered Events: (none)
  #~ Information: 0x75f0470
  #~ Data Released: False
  #~ Global Release Data: Off
  #~ UpdateTime: 0
  #~ Field Data:
    #~ Debug: Off
    #~ Modified Time: 4084397
    #~ Reference Count: 1
    #~ Registered Events: (none)
    #~ Number Of Arrays: 0
    #~ Number Of Components: 0
    #~ Number Of Tuples: 0
  #~ Number Of Children: 1
  #~ Child 0: vtkMultiBlockDataSet
    #~ Debug: Off
    #~ Modified Time: 4084412
    #~ Reference Count: 1
    #~ Registered Events: (none)
    #~ Information: 0x75f00e0
    #~ Data Released: False
    #~ Global Release Data: Off
    #~ UpdateTime: 0
    #~ Field Data:
      #~ Debug: Off
      #~ Modified Time: 4084404
      #~ Reference Count: 1
      #~ Registered Events: (none)
      #~ Number Of Arrays: 0
      #~ Number Of Components: 0
      #~ Number Of Tuples: 0
    #~ Number Of Children: 1
    #~ Child 0: vtkPolyData
      #~ Debug: Off
      #~ Modified Time: 4083744
      #~ Reference Count: 1
      #~ Registered Events: (none)
      #~ Information: 0x75eccb0
      #~ Data Released: False
      #~ Global Release Data: Off
      #~ UpdateTime: 0
      #~ Field Data:
        #~ Debug: Off
        #~ Modified Time: 4083721
        #~ Reference Count: 1
        #~ Registered Events: (none)
        #~ Number Of Arrays: 0
        #~ Number Of Components: 0
        #~ Number Of Tuples: 0
      #~ Number Of Points: 2
      #~ Number Of Cells: 2
      #~ Cell Data:
        #~ Debug: Off
        #~ Modified Time: 4083736
        #~ Reference Count: 1
        #~ Registered Events: (none)
        #~ Number Of Arrays: 3
        #~ Array 0 name = alpha.liquid
        #~ Array 1 name = p_rgh
        #~ Array 2 name = U
        #~ Number Of Components: 5
        #~ Number Of Tuples: 2
        #~ Copy Tuple Flags: ( 1 1 1 1 1 0 1 1 )
        #~ Interpolate Flags: ( 1 1 1 1 1 0 0 1 )
        #~ Pass Through Flags: ( 1 1 1 1 1 1 1 1 )
        #~ Scalars: (none)
        #~ Vectors: (none)
        #~ Normals: (none)
        #~ TCoords: (none)
        #~ Tensors: (none)
        #~ GlobalIds: (none)
        #~ PedigreeIds: (none)
        #~ EdgeFlag: (none)
      #~ Point Data:
        #~ Debug: Off
        #~ Modified Time: 4083744
        #~ Reference Count: 1
        #~ Registered Events: (none)
        #~ Number Of Arrays: 5
        #~ Array 0 name = alpha.liquid
        #~ Array 1 name = p_rgh
        #~ Array 2 name = U
        #~ Array 3 name = Normals
        #~ Array 4 name = aFun
        #~ Number Of Components: 9
        #~ Number Of Tuples: 2
        #~ Copy Tuple Flags: ( 1 1 1 1 1 0 1 1 )
        #~ Interpolate Flags: ( 1 1 1 1 1 0 0 1 )
        #~ Pass Through Flags: ( 1 1 1 1 1 1 1 1 )
        #~ Scalars: 
          #~ Debug: Off
          #~ Modified Time: 1693621
          #~ Reference Count: 10
          #~ Registered Events: (none)
          #~ Name: aFun
          #~ Data type: double
          #~ Size: 2
          #~ MaxId: 1
          #~ NumberOfComponents: 1
          #~ Information: 0x1b7713c0
            #~ Debug: Off
            #~ Modified Time: 1693932
            #~ Reference Count: 1
            #~ Registered Events: (none)
            #~ PER_COMPONENT: vtkInformationVector(0x183e4f80)
          #~ Name: aFun
          #~ Number Of Components: 1
          #~ Number Of Tuples: 2
          #~ Size: 2
          #~ MaxId: 1
          #~ LookupTable: (none)
          #~ Array: 0x1b7ec050
        #~ Vectors: (none)
        #~ Normals: 
          #~ Debug: Off
          #~ Modified Time: 1693604
          #~ Reference Count: 9
          #~ Registered Events: (none)
          #~ Name: Normals
          #~ Data type: float
          #~ Size: 6
          #~ MaxId: 5
          #~ NumberOfComponents: 3
          #~ Information: 0x18132690
            #~ Debug: Off
            #~ Modified Time: 1693955
            #~ Reference Count: 1
            #~ Registered Events: (none)
            #~ L2_NORM_RANGE: 0.999997 0.999999
            #~ PER_COMPONENT: vtkInformationVector(0x180fb0c0)
          #~ Name: Normals
          #~ Number Of Components: 3
          #~ Number Of Tuples: 2
          #~ Size: 6
          #~ MaxId: 5
          #~ LookupTable: (none)
          #~ Array: 0x1b4dbc10
        #~ TCoords: (none)
        #~ Tensors: (none)
        #~ GlobalIds: (none)
        #~ PedigreeIds: (none)
        #~ EdgeFlag: (none)
      #~ Bounds: 
        #~ Xmin,Xmax: (0, 0)
        #~ Ymin,Ymax: (-0.00598703, 0.00598202)
        #~ Zmin,Zmax: (3e-05, 3e-05)
      #~ Compute Time: 4084641
      #~ Number Of Points: 2
      #~ Point Coordinates: 0x183f9960
      #~ Locator: 0
      #~ Number Of Vertices: 2
      #~ Number Of Lines: 0
      #~ Number Of Polygons: 0
      #~ Number Of Triangle Strips: 0
      #~ Number Of Pieces: 1
      #~ Piece: -1
      #~ Ghost Level: 0
