#!/bin/bash
# PBS batch resources
#PBS -l mem=6000mb
#PBS -l nodes=1:ppn=6
#PBS -l walltime=3:50:00
#PBS -j oe
module load languages/python-3.3.2
python /newhome/pu17449/src/setup_scripts/mizuRoute/qsub_multiproc.py
