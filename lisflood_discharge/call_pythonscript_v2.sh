#!/bin/bash
# PBS batch resources
#PBS -l nodes=1:ppn=16
#PBS -l walltime=23:50:00
#PBS -j oe
module load languages/python-anaconda3-2019.03
#module load apps/gdal-2.3.1
#cd $PBS_O_WORKDIR
#cd /newhome/pu17449/data/lisflood/ancil_data/lisfloodfp_d89s_RectTest
#cd /newhome/pu17449/data/lisflood/ancil_data/lisfloodfp_rectclip_9sd8
#export OMP_NUM_THREADS=4

# ENV vars used by this script (exported by submit script):
# LISFLOOD_DIR and CONTROL_SCRIPT

# LISFLOOD_DIR is the working directory (env var exported by submit script)
echo "CDing to lisflood_dir $LISFLOOD_DIR"
cd $LISFLOOD_DIR

# Call python CONTROL_SCRIPT
# ENV VARS needed (exported by submit script):  CONTROL_FLIST, EXE_FILE, LOGDIR
# ENV VARS needed (set by QSUB):                OMP_NUM_THREADS, NCPUS
echo "Calling python control script $CONTROL_SCRIPT"
python $CONTROL_SCRIPT 
echo "Done"
