# Packages
import os,sys
from colabdesign.af import mk_af_model
import argparse
import glob
import yaml
import numpy as np
import pandas as pd

# Get arguments
def getArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", type=str)                    # Experiment Folder
    parser.add_argument("--output", "-o", type=str)                   # Output Folder
    parser.add_argument("--num_recycles", "-r", type=int)             # Number of recycles (>1)
    parser.add_argument("--use_multimer", "-m", type=str)             # Use multimer
    args = parser.parse_args()
    if args.use_multimer == "False":
        use_multimer = False
    return args, use_multimer

# Check if results folder exist
def checkResults(input:str):
    if not os.path.exists(input):
        raise Exception("Input folder does not exist")
    if not os.path.exists(f"{input}/Validation"):
        raise Exception("Validation folder does not exist")

# Get contig string
def getContig(config:str):
    configArgs = yaml.safe_load(open(config))
    contig = configArgs["diffusion"]["contigs"]
    return contig

# Get info about contig
def get_info(contig):
    F = []
    free_chain = False
    fixed_chain = False
    sub_contigs = [x.split("-") for x in contig.split("/")]
    for n,(a,b) in enumerate(sub_contigs):
        if a[0].isalpha():
            L = int(b)-int(a[1:]) + 1
            F += [1] * L
            fixed_chain = True
        else:
            L = int(b)
            F += [0] * L
            free_chain = True
    return F,[fixed_chain,free_chain]

# Create af model
def initModel(flags, protocol):
    if protocol == 'partial':
        af_model = mk_af_model(protocol='fixbb',use_templates=True,**flags)
    else:
        af_model = mk_af_model(protocol="fixbb",**flags)
    return af_model

# Run af
def runAF(af_model, seq, args, outdir, id):
    # Predict structure
    af_model.predict(seq=seq, num_recycles=args.num_recycles, verbose=False)
    # Save pdb file
    af_model.save_current_pdb(f"{outdir}/{id}.pdb")
    return af_model.aux["log"]

# Get fasta seq
def getSeq(path:str):
    fasta = glob.glob(path)[0]
    with open(fasta,"r") as f:
        entries = f.read().splitlines() 
    return entries

# Repeat AF predictions for RFdiffusion experiment
def predict(entries:list, args:dict, af_model, exp:str, af_terms:list, prep_flags:dict, outdir:str):
    print("Number of entries: ", len(entries))
    current_design = -1
    contig = ""
    out = {}
    data = []
    seq_number = 0
    labels = ["design","n","score"] + af_terms + ["seq"]
    for i in range(0, len(entries), 2):
        header = entries[i]
        seq = entries[i+1]
        print(header, seq)
        design_number = int(header.split(" ")[0].split(":")[-1])
        score = float(header.split("|")[1].split(":")[-1])
        print("Design Number: ", design_number)
        if design_number != current_design:
            if seq_number > 0:
                data += [[out[k][n] for k in labels] for n in range(seq_number+1)]
            seq_number = 0
            out['design'] = [design_number]
            out['n'] = [seq_number]
            out['seq'] = [seq]
            out['score'] = [score]
            for k in af_terms: out[k] = []
            pdb_filename = f"{args.input}/Diffusion/{exp}_{design_number}.pdb"
            af_model.prep_inputs(pdb_filename, **prep_flags)
            current_design = design_number
        else:
            seq_number += 1
            out["design"].append(design_number)
            out["n"].append(seq_number)
            out["seq"].append(seq)
            out["score"].append(score)
        
        id = f"design{design_number}_n{seq_number}"
        results = runAF(af_model=af_model, seq=seq, args=args, outdir=f"{outdir}/all_pdb", id=id)
        for t in af_terms: out[t].append(results[t])
        if "i_pae" in out:
          out["i_pae"][-1] = out["i_pae"][-1] * 31
        if "pae" in out:
          out["pae"][-1] = out["pae"][-1] * 31
        print("out after", out)
        af_model._k += 1
    print("before: ", data)
    data += [[out[k][n] for k in labels] for n in range(seq_number+1)]
    print(data)
    labels[2] = "mpnn"
    df = pd.DataFrame(data, columns=labels)
    df.to_csv(f'{outdir}/mpnn_results.csv')

"""
EXAMPLE
"""

# af_model = mk_af_model(protocol="fixbb",**flags)
# prep_flags = {"chain":"A",
#             "copies":1,
#             "homooligomer":False}
# af_terms = ["plddt","ptm","pae","rmsd"]
# pdb_filename = "Diffusion/Exp1_0_A_0.pdb"
# seq = "MEIYVFSAEEGDEKVVAKIEKKLKELKKEGKKVILVISVKSGNLEALEKLLDLAEKLKLEKVYVPADTGAHGKPEVRARAKELGATIGEFKGHVESAIAVAKEAYEDGKDKVIVIYAGSKEMEERILKAIKEK"
# num_recycles = 3
# af_model.prep_inputs(pdb_filename, **prep_flags)
# af_model.predict(seq=seq, num_recycles=num_recycles, verbose=False)
# print(af_model.aux["log"])

