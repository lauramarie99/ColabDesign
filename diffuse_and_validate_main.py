# Packages
import sys, random, string, re, os
if 'RFdiffusion' not in sys.path:
  os.environ["DGLBACKEND"] = "pytorch"
  sys.path.append('RFdiffusion')
import yaml
import argparse
import time
import diffuse_and_validate_utils as utils

# Get config
parser = argparse.ArgumentParser()
parser.add_argument('--config', type=str, required=True)
args = parser.parse_args()
args = yaml.safe_load(open(args.config))
args_diffusion = args["diffusion"]
args_validation = args["validation"]

# Check if output directory already exists
path = args_diffusion["name"]
if os.path.exists(f"outputs/{path}_0.pdb"):
  args_diffusion["name"] = path = args_diffusion["name"] + "_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))

# Get diffusion arguments
for k,v in args_diffusion.items():
  if isinstance(v,str):
    args_diffusion[k] = v.replace("'","").replace('"','')

# Run diffusion
contigs, copies = utils.run_diffusion(**args_diffusion)

# Print output contigs
print("the final contigs are:")
print(contigs)

# Wait until AlphaFold parameters are downloaded
if not os.path.isfile("params/done.txt"):
  print("downloading AlphaFold params...")
  while not os.path.isfile("params/done.txt"):
    time.sleep(5)

# Get ProteinMPNN and AlphaFold arguments
contigs_str = ":".join(contigs)
num_seqs = args_validation["num_seqs"]
num_recycles = args_validation["num_recycles"]
rm_aa = args_validation["rm_aa"]
num_designs = args_diffusion["num_designs"]

opts = [f"--pdb=outputs/{path}_0.pdb",
        f"--loc=outputs/{path}",
        f"--contig={contigs_str}",
        f"--copies={copies}",
        f"--num_seqs={num_seqs}",
        f"--num_recycles={num_recycles}",
        f"--rm_aa={rm_aa}",
        f"--num_designs={num_designs}"]
if args_validation["initial_guess"]: opts.append("--initial_guess")
if args_validation["use_multimer"]: opts.append("--use_multimer")
opts = ' '.join(opts)

# Run validation script (ProteinMPNN + AlphaFold)
print("running designability...")
print(f"python3.9 ./colabdesign/rf/designability_test.py {opts}")
os.system(f"python3.9 ./colabdesign/rf/designability_test.py {opts}")