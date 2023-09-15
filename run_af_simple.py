import os
import pandas as pd
from run_af import getArgs, getSeq, initModel, runAF

af_terms = ["plddt","ptm","pae","rmsd"]
args, use_multimer = getArgs()
entries = getSeq(f'{args.input}/*.fasta')
flags = {"best_metric":"rmsd",
        "use_multimer":use_multimer,
        "model_names":["model_1_multimer_v3" if use_multimer else "model_1_ptm"]}
af_model = initModel(flags=flags, protocol="fixbb")
prep_flags = {"chain":"A",
                "copies":1,
                "homooligomer":False}
outdir = args.output
if not os.path.exists(outdir):
    os.makedirs(outdir)

data = {}
for i in range(0,len(entries), 2):
    out = {}
    header = entries[i]
    seq = entries[i+1]
    pdb_id = header[1:].split(' ')[0][0:4]
    pdb_filename = f"{args.input}/pdbs/{pdb_id}_A.pdb"
    print(pdb_filename)
    af_model.prep_inputs(pdb_filename, **prep_flags)
    id = f"{pdb_id}_af"
    results = runAF(af_model=af_model, seq=seq, args=args, outdir=outdir, id=id)
    for t in af_terms: out[t]=results[t]
    if "i_pae" in out:
          out["i_pae"] = out["i_pae"] * 31
    if "pae" in out:
        out["pae"] = out["pae"] * 31
    data[pdb_id] = out
    af_model._k += 1
df = pd.DataFrame(data)
df.to_csv(f'{outdir}/af_predictions.csv')

