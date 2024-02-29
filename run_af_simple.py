"""
Run AlphaFold predictions, Specify folder with fasta file and crystal structures for comparison
"""

# Packages
import os
import pandas as pd
from af_utils import getArgs, getSeq, initModel, runAF

"""
Arguments
--input, -i, type=str                   # Experiment folder with fasta file
--output, -o, type=str                  # Output folder
--num_recycles, -r, type=int            # Number of recycles (>1)
--use_multimer, -m, type=str            # Use multimer
"""

# Read arguments
af_terms = ["plddt","ptm","pae","rmsd"]
args, use_multimer = getArgs()
entries = getSeq(f'{args.input}/*.fasta')
flags = {"best_metric":"rmsd",
         "use_multimer":use_multimer,
         "model_names":["model_1_multimer_v3" if use_multimer else "model_1_ptm"]}

# Initialize AF model
af_model = initModel(flags=flags, protocol="fixbb")
prep_flags = {"chain":"A",
              "copies":1,
              "homooligomer":False}
if not os.path.exists(args.output):
    os.makedirs(args.output)

# Make prediction and save results
data = {}
for i in range(0, len(entries), 2):
    out = {}
    header = entries[i]
    seq = entries[i+1]
    pdb_id = header[1:].split(' ')[0][0:4]
    pdb_filename = f"{args.input}/{pdb_id}.pdb"                                         # Get crystal structure for comparison
    print(pdb_filename)
    af_model.prep_inputs(pdb_filename, **prep_flags)
    id = f"{pdb_id}_af"
    results = runAF(af_model=af_model, seq=seq, args=args, outdir=args.output, id=id)
    for t in af_terms: out[t]=results[t]
    if "i_pae" in out:
          out["i_pae"] = out["i_pae"] * 31
    if "pae" in out:
        out["pae"] = out["pae"] * 31
    data[pdb_id] = out
    af_model._k += 1
df = pd.DataFrame(data)
df.to_csv(f'{args.output}/af_predictions.csv')

