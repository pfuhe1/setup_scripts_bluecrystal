#!/bin/bash
# PBS batch resources
#PBS -l mem=16000mb
#PBS -l nodes=1:ppn=16
#PBS -l walltime=11:50:00
#PBS -j oe
module load languages/python-3.3.2
module load languages/intel-compiler-16-u2 
module load libraries/intel_builds/netcdf-4.3 
module load libraries/intel_builds/hdf5-1.8.12
module list

python /newhome/pu17449/src/setup_scripts/fuse_GBM/qsub_GBMrun.py
