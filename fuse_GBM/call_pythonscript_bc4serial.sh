#!/bin/bash
#SBATCH --job-name=fuse_catchments_serial
#SBATCH --partition=serial
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCh --cpus-per-task=1
#SBATCH --mem=1000mb
#SBATCH --time=47:50:00

# Load packages
module purge
module load languages/anaconda3/2018.12
module load OpenMPI/1.10.3-GCC-5.4.0-2.26 # note openmpi needs to be loaded before intel
module load intel/2017.01
# Add netcdf and hdf5 paths (loading module conflicts with the intel module)
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/mnt/storage/software/libraries/intel/hdf5-1.10.1-mpi/lib:/mnt/storage/software/libraries/intel/netcdf-4.4.1.1-mpi/lib
#module load libs/netcdf/4.4.1.1.MPI
module load Szip/2.1-foss-2016b
module list

python /mnt/storage/home/pu17449/src/setup_scripts/fuse_GBM/qsub_GBMrun.py
