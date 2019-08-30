#!/bin/bash
# PBS batch resources
#PBS -l mem=16000mb
#PBS -l nodes=1:ppn=16
#PBS -l walltime=11:50:00
#PBS -j oe
module load languages/python-3.3.2
python /newhome/pu17449/src/setup_scripts/fuse_GBM/qsub_GBMrun.py
