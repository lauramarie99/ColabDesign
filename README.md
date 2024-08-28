# Protein/Enzyme Design with RFdiffusion and ProteinMPNN
Proteins are designed using RFdiffusion based on given constraints. 
Sequences are generated using ProteinMPNN and validated using AlphaFold2. Have fun!

New updated repository: https://github.com/lauramarie99/ProtDesign

## Overview
- diffuse.py: Diffusion (RFdiffusion or RFdiffusion all-atom)
- validate.py: Validation (ProteinMPNN + AF2)
- configs: Folder containing example config files for diffusion and validation
- run_cluster.py: Slurm script generation and job submission to cluster
- RFdiffusion_dockerfile: Dockerfile for RFdiffusion step
- Validation_GPU_dockerfile: Dockerfile for validation step

## Setup

### ColabDesign
- Clone this repository
- cd into ColabDesign repository
- Get AF models
```
mkdir params
aria2c -q -x 16 https://storage.googleapis.com/alphafold/alphafold_params_2022-12-06.tar
tar -xf alphafold_params_2022-12-06.tar -C params
touch params/done.txt
```
- Build container using Validation_GPU_dockerfile

### RFdiffusion
- Clone RFdiffusion repository (https://github.com/lauramarie99/RFdiffusion)
- cd into RFdiffusion repository
- Get RF models
```
mkdir models && cd models
wget http://files.ipd.uw.edu/pub/RFdiffusion/6f5902ac237024bdd0c176cb93063dc4/Base_ckpt.pt
wget http://files.ipd.uw.edu/pub/RFdiffusion/5532d2e1f3a4738decd58b19d633b3c3/ActiveSite_ckpt.pt
```
- Build docker/singularity container based on provided dockerfile RFdiffusion_dockerfile
- Adapt path to RFdiffusion in diffuse.py


### RFdiffusion all-atom
- Clone RFdiffusion all-atom repository (https://github.com/lauramarie99/rf_diffusion_all_atom)
- cd into RFdiffusion all-atom repository
- Download the model weights
```
wget http://files.ipd.uw.edu/pub/RF-All-Atom/weights/RFDiffusionAA_paper_weights.pt
```
- Download the singularity container
```
wget http://files.ipd.uw.edu/pub/RF-All-Atom/containers/rf_se3_diffusion.sif
```
- Initialize git submodules
```
git submodule init
git submodule update
```
- Adapt path to RFdiffusion all-atom in diffuse.py

## Get started
For the diffusion and validation (ProteinMPNN + AF) steps, only one single config file is used. Example config files can be found in the folder configs.
- type: base (RFdiffusion) or all-atom (RFdiffusion all-atom)
- ckpt_override_path: Override RFdiffusion model path (e.g. Active_Site model)
- contigs: Contig string (Specify always a range, e.g. 16-16 instead of 16!)
- enzyme_design: Set true if you want to use an external potential
- guide_potentials: External potential to use (only used if enzyme_design = true)
- guide_scale: Scale factor for guide potential (only used if enzyme_design = true)
- substrate: Substrate name (only used if enzyme_design = true OR type = all-atom)
- iterations: Number of RFdiffusion steps
- name: Experiment name
- noise scale: RFdiffusion noise scale
- num_designs: Number of designs to generate with RFdiffusion
- path: Directory where to store results
- pdb: Input structure (The structure where the fixed residues are taken from)
- num_recycles: Number of AF2 recycles
- num_seqs: Number of ProteinMPNN sequences to generate
- rm_aa: Avoid using specific aa, e.g. cysteines
- use_multimer: Use AF multimer?

### Run diffusion
```
python3.9 diffuse.py --config config.yml
```

### Run validation
```
python3.8 validate.py --config config.yml
```

## Large scale studies
For generation of many config files based on a general config file, the script create_configs.py in the folder configs can be used.
An example general config file is experiment1.yml.

To automatically generate slurm scripts and submit the jobs, the script run_cluster.py can be used.
You need to modify the paths for your purposes.

## ColabDesign Contributors:
- Sergey Ovchinnikov [@sokrypton](https://github.com/sokrypton)
- Shihao Feng [@JeffSHF](https://github.com/JeffSHF)
- Justas Dauparas [@dauparas](https://github.com/dauparas)
- Weikun.Wu [@guyujun](https://github.com/guyujun) (from [Levinthal.bio](http://levinthal.bio/en/))
- Christopher Frank [@chris-kafka](https://github.com/chris-kafka)
