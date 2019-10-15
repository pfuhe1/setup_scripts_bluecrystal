#!/bin/bash
#SBATCH --job-name=fuse_catchments
#SBATCH --partition=cpu
#SBATCH --nodes=1
#SBATCH --ntasks-per-node = 28
#SBATCh --cpus-per-task=1
#SBATCH --mem=16000mb
#SBATCH --time=23:50:00

module load languages/anaconda3/2018.12
module load intel/2017.01
module load libs/netcdf/4.4.1.1.MPI
module list
python /mnt/storage/home/pu17449/src/setup_scripts/fuse_catchments/qsub_grdc_catch.py
