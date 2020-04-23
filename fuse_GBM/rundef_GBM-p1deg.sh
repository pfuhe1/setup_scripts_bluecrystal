# PBS batch resources
#PBS -l walltime=11:50:00
#PBS -l select=1:ncpus=1:mem=32gb
#PBS -j oe
module load lib/netcdf/4.70
/home/pu17449/src/fuse_dev/bin/fuse.exe /work/pu17449/fuse/GBM-p1deg/fm_files/fm_GBM-p1deg_MSWEP-ERA5_900.txt GBM-p1deg run_def

