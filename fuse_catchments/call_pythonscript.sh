#!/bin/bash
# PBS batch resources
#PBS -l mem=16000mb
#PBS -l nodes=1:ppn=16
#PBS -l walltime=23:50:00
#PBS -j oe
module load languages/python-3.3.2
python /newhome/pu17449/src/fuse/setup_scripts/qsub_grdc_catch.py
