#!/bin/bash
#SBATCH --job-name=lisflood-fp_run
#SBATCH --partition=cpu
#SBATCH --nodes=1
#SBATCH --time=72:00:00
# NOTE: some resources are passed through by the command line
# e.g.:
# --mem-per-cpu=4gb
# --ntasks-per-node=1
# --cpus-per-task=28


# Load packages
module purge
module load languages/anaconda3/2018.12
source activate petepy

#export OMP_NUM_THREADS=$SLURM_JOB_CPUS_PER_NODE
#export NCPUS=$SLURM_JOB_CPUS_PER_NODE
export

echo "Starting script"

# ENV vars used by this script (exported by submit script):
# LISFLOOD_DIR and CONTROL_SCRIPT

# LISFLOOD_DIR is the working directory (env var exported by submit script)
echo "CDing to lisflood_dir $LISFLOOD_DIR"
cd $LISFLOOD_DIR

# Call python CONTROL_SCRIPT
# ENV VARS needed (exported by submit script):  CONTROL_FLIST, EXE_FILE, LOGDIR
# ENV VARS needed (set by QSUB, or above for slurm):      OMP_NUM_THREADS, NCPUS
echo "Calling python control script $CONTROL_SCRIPT"
python $CONTROL_SCRIPT
echo "Done"
