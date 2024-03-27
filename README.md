# Protein/Enzyme Design with RFdiffusion and ProteinMPNN
Proteins are designed using RFdiffusion based on given constraints. 
Sequences are generated using ProteinMPNN and validated using AlphaFold.\
Have fun!

## Overview
- diffuse.py: Diffusion
- validate.py: Validation (ProteinMPNN + AF2)
- config_simple: Example config file for unconditional diffusion and validation
- config_enzyme: Example config file for enzyme design with external potential
- create_configs.py: Creates configs file based on experimental setup (for large studies)
- run_cluster.py: Automate slurm script generation and job submission in cluster
- Dockerfile_cluster: Dockerfile for diffusion step
- diffuse_and_validate.py: Diffusion and Validation in one script (not recommended)

## Setup
- Build docker/singularity container (only docker file for diffusion step provided)
- Clone this repository
- Clone RFdiffusion repository (https://github.com/sokrypton/RFdiffusion)
- Change path of RFdiffusion repo in diffuse.py
- cd into RFdiffusion repository
- Get RF models \

```
mkdir models && cd models
wget http://files.ipd.uw.edu/pub/RFdiffusion/6f5902ac237024bdd0c176cb93063dc4/Base_ckpt.pt
wget http://files.ipd.uw.edu/pub/RFdiffusion/5532d2e1f3a4738decd58b19d633b3c3/ActiveSite_ckpt.pt
```
- cd into ColabDesign repository
- Get AF models

```
mkdir params
aria2c -q -x 16 https://storage.googleapis.com/alphafold/alphafold_params_2022-12-06.tar
tar -xf alphafold_params_2022-12-06.tar -C params
touch params/done.txt
```

## Get started
For the diffusion and validation (ProteinMPNN + AF) steps one contig file is used. It contains all information needed.
- ckpt_override_path: RFdiffusion model (Base or Active_Site model)
- contigs: Contig string (Specify always a range, e.g. 16-16 instead of 16!)
- enzyme_design: Set true if you want to use an external potential
- guide_potentials: External potential to use
- iterations: Number of diffusion steps
- name: Experiment name
- noise scale: RFdiffusion noise scale
- num_designs: Number of designs to generate with RFdiffusion
- path: Directory where to store results
- pdb: Input structure (the structure where the fixed residues are taken from)
- substrate: Substrate name (needed for external potential)
- symmetry: Symmetry settings
- num_recycles: AF recycles
- num_seqs: Number of ProteinMPNN sequences
- rm_aa: Avoid using specific aa, e.g. cysteines
- use_multimer: Use AF multimer?

### Run diffusion
```
python3.9 diffuse.py --config config.yml
```

### Run validation
```
python3 validate.py --config config.yml
```

## Large scale studies
For generation of many config files based on a general config file, the script create_configs.py can be used.
An example general config file is experiment1.yml.

To automatically generate slurm scripts and submit the jobs, the script run_cluster.py can be used.
You need to modify the paths for your purposes.

### ColabDesign Contributors:
- Sergey Ovchinnikov [@sokrypton](https://github.com/sokrypton)
- Shihao Feng [@JeffSHF](https://github.com/JeffSHF)
- Justas Dauparas [@dauparas](https://github.com/dauparas)
- Weikun.Wu [@guyujun](https://github.com/guyujun) (from [Levinthal.bio](http://levinthal.bio/en/))
- Christopher Frank [@chris-kafka](https://github.com/chris-kafka)
