import os,sys
from colabdesign.af import mk_af_model
import argparse
import glob
import yaml
import numpy as np
import pandas as pd
from run_af import *

# MAIN 
af_terms = ["plddt","ptm","pae","rmsd"]
copies = 1
args, use_multimer = getArgs() # get arguments
entries = getSeq(f"{args.input}/Validation/*.fasta") # get sequences
config = glob.glob(f"{args.input}/*.yml")[0] # get config
contig = getContig(config) # get contig string
pos,(fixed_chain,free_chain) = get_info(contig) # get info

fixed_chains = fixed_chain and not free_chain
free_chains = free_chain and not fixed_chain
both_chains = fixed_chain and free_chain

flags = {"best_metric":"rmsd",
        "use_multimer":use_multimer,
        "model_names":["model_1_multimer_v3" if use_multimer else "model_1_ptm"]}

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
else:
    protocol = "fixbb"
    print("protocol=fixbb")
    af_model = initModel(flags=flags, protocol="fixbb")
    prep_flags = {"chain":"A",
                "copies":copies,
                "homooligomer":copies>1}

exp = args.input.split("/")[-1]
outdir = f"{args.input}/{args.output}"
if not os.path.exists(outdir):
    os.makedirs(f"{outdir}/all_pdb")
predict(entries=entries, args=args, af_model=af_model, exp=exp, af_terms=af_terms,prep_flags=prep_flags, outdir=outdir)
file = open(f"{outdir}/config.yml","w")
yaml.dump(args, file)

