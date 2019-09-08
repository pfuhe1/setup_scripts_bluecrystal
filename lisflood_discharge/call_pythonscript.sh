#!/bin/bash
# PBS batch resources
#PBS -l nodes=1:ppn=16
#PBS -l walltime=21:50:00
#PBS -j oe
module load languages/python-anaconda3-2019.03
#module load apps/gdal-2.3.1
#cd $PBS_O_WORKDIR
cd /newhome/pu17449/data/lisflood/ancil_data/lisfloodfp_d89s_RectTest
export OMP_NUM_THREADS=8
python /newhome/pu17449/src/setup_scripts/lisflood_discharge/qsub_multiproc.py
