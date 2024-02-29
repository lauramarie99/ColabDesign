"""
Re-Run AlphaFold predictions for RFdiffusion experiment
"""

# Packages
import os,sys
from colabdesign.af import mk_af_model
import argparse
import glob
import yaml
import numpy as np
import pandas as pd
from af_utils import *

"""
Arguments
--input, -i, type=str                   # Experiment folder from RFdiffusion experiment (contains Diffusion and Validation results)
--output, -o, type=str                  # Output folder
--num_recycles, -r, type=int            # Number of recycles (>1)
--use_multimer, -m, type=str            # Use multimer
"""

# Read arguments
af_terms = ["plddt","ptm","pae","rmsd"]
copies = 1
args, use_multimer = getArgs()                              # Get arguments
entries = getSeq(f"{args.input}/Validation/*.fasta")        # Get sequences from validation
config = glob.glob(f"{args.input}/*.yml")[0]                # Get config
contig = getContig(config)                                  # Get contig string
pos, (fixed_chain,free_chain) = get_info(contig)            # Get info

fixed_chains = fixed_chain and not free_chain
free_chains = free_chain and not fixed_chain
both_chains = fixed_chain and free_chain

flags = {"best_metric":"rmsd",
         "use_multimer":use_multimer,
         "model_names":["model_1_multimer_v3" if use_multimer else "model_1_ptm"]}

# Partial diffusion (Template used)
if sum(pos) > 0:
    protocol = "partial"
    print("protocol=partial")
    af_model = initModel(flags=flags, protocol="partial")
    rm_template = np.array(pos) == 0
    prep_flags = {"chain":"A",
                  "rm_template":rm_template,
                  "rm_template_seq":rm_template,
                  "copies":copies,
                  "homooligomer":copies>1}

# Normal AF prediction
else:
    protocol = "fixbb"
    print("protocol=fixbb")
    af_model = initModel(flags=flags, protocol="fixbb")
    prep_flags = {"chain":"A",
                  "copies":copies,
                  "homooligomer":copies>1}

# Save results
exp = args.input.split("/")[-1]
outdir = f"{args.input}/{args.output}"
if not os.path.exists(outdir):
    os.makedirs(f"{outdir}/all_pdb")
predict(entries=entries, args=args, af_model=af_model, exp=exp, af_terms=af_terms,prep_flags=prep_flags, outdir=outdir)
file = open(f"{outdir}/config.yml","w")
yaml.dump(args, file)

