#!/bin/bash
#PBS -S /bin/bash
#PBS -M isozm@vscht.cz
#PBS -m bae
#PBS -N 
#PBS -q batch
#PBS -l nodes=1:ppn=
#PBS -l walltime=

# testovaci uloha pro OpenFOAM - verze 2
# nastaveni prostredi
export PATH=$PATH:/usr/lib64/mpi/gcc/openmpi/bin
export OMPI_MCA_btl="sm,self"

export FOAM_INST_DIR=/opt/OpenFOAM/
foamDotFile="$FOAM_INST_DIR/OpenFOAM-2.4.0/etc/bashrc foamCompiler=ThirdParty WM_COMPILER=Gcc48 WM_MPLIB=SYSTEMOPENMPI"
. $foamDotFile

caseDir=''

# copy the necessary files to scratch
cp -r ~/$caseDir /scratch/isozm/$caseDir

# spusteni vypoctu
cd /scratch/isozm/$caseDir
./Allrun-parallel

# copy all the results back to the home folder (no need for the 'processor*' folders)
cd ~
rsync -a /scratch/isozm/$caseDir/ ~/$caseDir/ --exclude "processor*"
