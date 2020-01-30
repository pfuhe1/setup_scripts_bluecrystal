#!/bin/sh
# PBS batch resources
#PBS -l select=2::ncpus=24
#PBS -l walltime=23:50:00
#PBS -j oe

# Load modules for blue pebble
module load lib/gdal/2.4.2
module load lang/python/anaconda/3.7-2019.03

# LISFLOOD_DIR is the working directory (env var exported by submit script)
cd $LISFLOOD_DIR

# Call python control script
# ENV VARS used (exported by submit script):
# CONTROL_FLIST, OMP_NUM_THREADS, EXE_FILE, , NODESIZE, LOGDIR
python /newhome/pu17449/src/setup_scripts/lisflood_discharge/qsub_multiproc.py
