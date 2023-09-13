## README not up to date!!

# Protein Design with RFDiffusion and ProteinMPNN
Proteins are designed using RFDiffusion based on given constraints. 
Sequences are generated using ProteinMPNN and validated using AlphaFold.\
Have fun!

## Overview
- diffuse.py: Diffusion
- validate.py: Validation (ProteinMPNN + AF2)
- config_simple: Example config file for unconditional diffusion and validation
- config_enzyme: Example config file for enzyme design with external potential
- create_configs.py: Creates configs file based on experimental setup
- run_cluster.py: Automate slurm job submission in cluster
- Dockerfile_cluster: Dockerfile
- diffuse_and_validate.py: Diffusion and Validation in one script

## Setup
- Build docker container
- Clone repository
- Clone RFDiffusion repo inside ColabDesign repo (https://github.com/sokrypton/RFdiffusion)
- Make outputs directory and get RF models \
``mkdir outputs``\
``mkdir models && cd models`` \
``wget http://files.ipd.uw.edu/pub/RFdiffusion/6f5902ac237024bdd0c176cb93063dc4/Base_ckpt.pt`` \
``wget http://files.ipd.uw.edu/pub/RFdiffusion/5532d2e1f3a4738decd58b19d633b3c3/ActiveSite_ckpt.pt``
- Get AF models \
``mkdir params`` \
``aria2c -q -x 16 https://storage.googleapis.com/alphafold/alphafold_params_2022-12-06.tar``\
``tar -xf alphafold_params_2022-12-06.tar -C params`` \
``touch params/done.txt``

## Get started
For diffusion and validation the same contig is used. It contains all information needed.

### Run diffusion
``python3.9 diffuse.py --config config.yml``

### Run validation
``python3.9 diffuse.py --config config.yml``

## Config Generation
For generation of the config files, the script create_configs.py can be used.


# ColabDesign
### Making Protein Design accessible to all via Google Colab! 
- P(structure | sequence)
  - [TrDesign](/tr) - using TrRosetta for design
  - [AfDesign](/af) - using AlphaFold for design
  - [WIP] [RfDesign](https://github.com/RosettaCommons/RFDesign) - using RoseTTAFold for design
- P(sequence | structure)
  - [ProteinMPNN](/mpnn)
  - [WIP] TrMRF
- P(sequence)
  - [WIP] [MSA_transformer](/esm_msa)
  - [WIP] [SEQ](/seq) - (GREMLIN, mfDCA, arDCA, plmDCA, bmDCA, etc)
- P(structure)
  - [Rfdiffusion](/rf)

### Where can I chat with other ColabDesign users?
  - See our [Discord](https://discord.gg/gna8maru7d) channel!


### Presentations
[Slides](https://docs.google.com/presentation/d/1Zy7lf_LBK0_G3e7YQLSPP5aj_-AR5I131fTsxJrLdg4/)
[Talk](https://www.youtube.com/watch?v=2HmXwlKWMVs)

### Contributors:
- Sergey Ovchinnikov [@sokrypton](https://github.com/sokrypton)
- Shihao Feng [@JeffSHF](https://github.com/JeffSHF)
- Justas Dauparas [@dauparas](https://github.com/dauparas)
- Weikun.Wu [@guyujun](https://github.com/guyujun) (from [Levinthal.bio](http://levinthal.bio/en/))
- Christopher Frank [@chris-kafka](https://github.com/chris-kafka)
