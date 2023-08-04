# Packages
import sys, random, string, re, os
import yaml
import argparse
import time


# Check if AlphaFold parameters are downloaded
if not os.path.isfile("params/done.txt"):
    raise Exception("AlphaFold parameters not found...")

# Get config file
parser = argparse.ArgumentParser()
parser.add_argument('--config', type=str, required=True)
args = parser.parse_args()
args = yaml.safe_load(open(args.config))
args_validation = args["validation"]

# Get ProteinMPNN and AlphaFold arguments
contigs_str = args["diffusion"]["contigs"]
print(contigs_str)

num_seqs = args_validation["num_seqs"]
num_recycles = args_validation["num_recycles"]
rm_aa = args_validation["rm_aa"]
num_designs = args["diffusion"]["num_designs"]
path = args["diffusion"]["path"]
name = args["diffusion"]["name"]
full_path = f"{path}{name}"

opts = [f"--pdb={full_path}/Diffusion/{name}_0.pdb",
        f"--loc={full_path}/Validation",
        f"--contig={contigs_str}",
        f"--copies=1",
        f"--num_seqs={num_seqs}",
        f"--num_recycles={num_recycles}",
        f"--rm_aa={rm_aa}",
        f"--num_designs={num_designs}"]
if args_validation["initial_guess"]: opts.append("--initial_guess")
if args_validation["use_multimer"]: opts.append("--use_multimer")
opts = ' '.join(opts)

# Run validation script (ProteinMPNN + AlphaFold)
print("running designability...")
print(f"python3 ./colabdesign/rf/designability_test.py {opts}")
os.system(f"python3 ./colabdesign/rf/designability_test.py {opts}")
# !python colabdesign/rf/designability_test.py {opts}