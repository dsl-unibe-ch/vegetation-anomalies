#!/bin/bash
#SBATCH --job-name="Vegetation Anomalies Zarr to PNG Tiles Conversion"
#SBATCH --time=02:00:00
#SBATCH --mem-per-cpu=1G
#SBATCH --cpus-per-task=16

echo "Launched at $(date)"
echo "Job ID: ${SLURM_JOBID}"
echo "Node list: ${SLURM_NODELIST}"
echo "Submit dir.: ${SLURM_SUBMIT_DIR}"
echo "Numb. of cores: ${SLURM_CPUS_PER_TASK}"

echo "Current directory:"
pwd

echo "module local Anaconda3"
module load Anaconda3
eval "$(conda shell.bash hook)"

echo "conda create --name vegetation-anomalies"
conda create -y --name vegetation-anomalies

echo "conda activate vegetation-anomalies"
conda activate vegetation-anomalies

echo "conda install -y -c conda-forge gdal zarr"
conda install -y -c conda-forge gdal zarr

echo "pip install -r requirements.txt"
pip install -r requirements.txt

echo "python zarr_to-png_tiles.py ..."
python zarr_to_png_tiles.py ../data/larger-anomalies.zarr ../data/larger_cubes_demo_output 0-14 16

echo "conda deactivate"
conda deactivate
