# Packages
import sys, random, string, re, os, time
if 'RFdiffusion' not in sys.path:
  os.environ["DGLBACKEND"] = "pytorch"
  sys.path.append('RFdiffusion')
from IPython.display import display
import subprocess
import yaml
import argparse

# Run subprocess
def run(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
    while True:
        line = process.stdout.readline()
        if not line: break    
    return_code = process.wait()

# Run diffusion
def run_diffusion(type, contigs, name, path,
                  pdb=None, 
                  iterations=50,
                  num_designs=10,
                  guide_scale=1,
                  guide_potentials="",
                  substrate="2PE",
                  ckpt_override_path="null",
                  enzyme_design=False,
                  partial_diffusion=False,
                  noise_scale=1,
                  deterministic=False):
    """
    This function runs a diffusion simulation using provided input parameters, 
    applies contigs processing, and generates the final PDB structures.

    Args:
    contigs (str): Input contigs string to define the fixed and free portions.
    name (str): Experiment name.
    path (str): The output directory path for generated results.
    pdb (str, optional): The PDB file path. Defaults to None.
    iterations (int, optional): Number of diffusion iterations. Defaults to 50.
    num_designs (int, optional): Number of designs to generate. Defaults to 10.
    guide_scale (float): Scaling factor for guiding potentials. Defaults to 1.
    guide_potentials (str): The guiding potentials string. Defaults to an empty string.
    substrate (str): The substrate design. Defaults to "2PE".
    ckpt_override_path (str): The path of the checkpoint file. Defaults to "null".
    enzyme_design (bool, optional): If True, generates substrate pockets by adding guiding potential. Defaults to False.
    noise_scale (int, optional): Change noise_scale_ca and noise_scale_frame.
    deterministic (bool, optional): Deterministic initialization.
    
    Returns:
    tuple: The updated contigs list and the number of symmetry-equivalent copies.
    """

    from colabdesign.rf.utils import fix_contigs, fix_partial_contigs, fix_pdb, sym_it
    from colabdesign.shared.protein import pdb_to_string
    from rfdiffusion.inference.utils import parse_pdb
    # Make output directory
    full_path = f"{path}{name}/Diffusion"
    os.makedirs(full_path, exist_ok=True)
    output_prefix = f"{full_path}/{name}"

    # Add general options
    opts = [f"inference.output_prefix={output_prefix}", 
            f"inference.num_designs={num_designs}",
            f"denoiser.noise_scale_ca={noise_scale}",
            f"denoiser.noise_scale_frame={noise_scale}",
            f"inference.ckpt_override_path={ckpt_override_path}"]

    contigs = contigs.replace(",", " ").replace(":", " ").split()
    is_fixed, is_free = False, False
    fixed_chains = []

    # Iterate through contigs to identify fixed and free portions
    for contig in contigs:
        for x in contig.split("/"):
            a = x.split("-")[0]

            # Check if the first character is an alphabet (fixed segment)
            if a[0].isalpha():
                is_fixed = True
                if a[0] not in fixed_chains:
                    fixed_chains.append(a[0])

            # Check if the segment is purely numeric (free segment)
            if a.isnumeric():
                is_free = True

    # Set the mode based on the identified fixed and free portions
    if len(contigs) == 0 or not is_free:
        mode = "partial"
    elif is_fixed:
        mode = "fixed"
    else:
        mode = "free"

    copies = 1
    
    # Process contigs and options for fixed mode
    if mode == "fixed":
      
        # Get PDB string
        pdb_str = pdb_to_string(pdb, chains=fixed_chains)
        # Store input PDB in outdir
        pdb_filename = f"{full_path}/input.pdb"
        os.system(f"cp {pdb} {pdb_filename}")
        # Parse the PDB file and update options
        parsed_pdb = parse_pdb(pdb_filename)
        opts.append(f"inference.input_pdb={pdb_filename}")
        # Print prefix contigs for diagnostic purposes
        print("prefix contigs:", contigs)
        contigs = fix_contigs(contigs, parsed_pdb)
        print("fixed contigs:", contigs)
    
    # Process contigs and options for the free mode
    elif mode == "free":
        parsed_pdb = None
        contigs = fix_contigs(contigs, parsed_pdb)
    
    # Process contigs and options for the partial mode
    else:
       raise Exception("Partial mode is not implemented yet!")

    # Add contig to options
    opts.append(f"'contigmap.contigs=[{' '.join(contigs)}]'")

    # Add enzyme_design related options if enzyme_design is True
    if enzyme_design:
        opts.append(f"potentials.guide_scale={guide_scale}")
        opts.append(f"'potentials.guiding_potentials=[\"{guide_potentials}\"]'")
        opts.append(f"potentials.substrate={substrate}")

    # Add number of diffusion steps
    if partial_diffusion:
        opts.append(f"diffuser.partial_T={iterations}")
    else:
        opts.append(f"diffuser.T={iterations}")

    if deterministic:
        opts.append(f"inference.deterministic=True")

    # Print different parameters for diagnostic purposes
    print("mode:", mode)
    print("output:", full_path)
    print("contigs:", contigs)

    # Create the command with options to run the inference script
    opts_str = " ".join(opts)
    cmd = f"python3.9 ./RFdiffusion/run_inference.py {opts_str}"
    print(cmd)
    # Run the command using a helper function "run"
    run(cmd)

    # Post-processing: fix PDB structures based on contigs
    for n in range(num_designs):
        pdbs = [
            f"{full_path}/traj/{name}_{n}_pX0_traj.pdb",
            f"{full_path}/traj/{name}_{n}_Xt-1_traj.pdb",
            f"{output_prefix}_{n}.pdb"]

        for pdb in pdbs:
            with open(pdb, "r") as handle:
                pdb_str = handle.read()

            with open(pdb, "w") as handle:
                handle.write(fix_pdb(pdb_str, contigs))

    return contigs, copies

# Run diffusion
def run_diffusion_aa(type, contigs, name, path,
                    pdb=None, 
                    iterations=50,
                    num_designs=10,
                    partial_diffusion=False,
                    noise_scale=1,
                    deterministic=False,
                    substrate='2PE'):
    """
    This function runs a diffusion-all-atom simulation using provided input parameters, 
    applies contigs processing, and generates the final PDB structures.

    Args:
    contigs (str): Input contigs string to define the fixed and free portions.
    name (str): Experiment name.
    path (str): The output directory path for generated results.
    pdb (str, optional): The PDB file path. Defaults to None.
    iterations (int, optional): Number of diffusion iterations. Defaults to 50.
    num_designs (int, optional): Number of designs to generate. Defaults to 10.
    guide_scale (float): Scaling factor for guiding potentials. Defaults to 1.
    guide_potentials (str): The guiding potentials string. Defaults to an empty string.
    substrate (str): The substrate design. Defaults to "2PE".
    ckpt_override_path (str): The path of the checkpoint file. Defaults to "null".
    enzyme_design (bool, optional): If True, generates substrate pockets by adding guiding potential. Defaults to False.
    noise_scale (int, optional): Change noise_scale_ca and noise_scale_frame.
    deterministic (bool, optional): Deterministic initialization.
    
    Returns:
    tuple: The updated contigs list and the number of symmetry-equivalent copies.
    """

    # Make output directory
    full_path = f"{path}/{name}/Diffusion"
    os.makedirs(full_path, exist_ok=True)
    output_prefix = f"{full_path}/{name}"
    copies = 1

    # Add general options
    opts = [f"inference.output_prefix={output_prefix}", 
            f"inference.num_designs={num_designs}",
            f"denoiser.noise_scale_ca={noise_scale}",
            f"denoiser.noise_scale_frame={noise_scale}",
            f"diffuser.T={iterations}",
            f"inference.ligand={substrate}"]

    contigs = contigs.replace("/", ",").split()
    opts.append(f"'contigmap.contigs=[{' '.join(contigs)}]'")

    pdb_filename = f"{full_path}/input.pdb"
    os.system(f"cp {pdb} {pdb_filename}")
    opts.append(f"inference.input_pdb={pdb_filename}")

    if deterministic:
        opts.append(f"inference.deterministic=True")

    print("output:", full_path)
    print("contigs:", contigs)

    # Create the command with options to run the inference script
    opts_str = " ".join(opts)
    cmd = f"cd ./rf_diffusion_all_atom && python run_inference.py {opts_str}"
    print(cmd)
    # Run the command using a helper function "run"
    run(cmd)

    return contigs, copies


# Read given config
parser = argparse.ArgumentParser()
parser.add_argument('--config', type=str, required=True)
args = parser.parse_args()
config = args.config
args = yaml.safe_load(open(config))
args_diffusion = args["diffusion"]
args_validation = args["validation"]

# Check if output directory already exists
name = args_diffusion["name"]
path = args_diffusion["path"]
if os.path.exists(f"{path}{name}/Diffusion/{name}_0.pdb"):
  args_diffusion["name"] = name = args_diffusion["name"] + "_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))

# Get diffusion arguments
for k,v in args_diffusion.items():
  if isinstance(v,str):
    args_diffusion[k] = v.replace("'","").replace('"','')

# Run diffusion
if args_diffusion["type"] == "all-atom":
     contigs, copies = run_diffusion_aa(**args_diffusion)
else:
    contigs, copies = run_diffusion(**args_diffusion)

# Copy config to results directory
os.system(f"cp {config} {path}{name}/")

# Print output contigs
print("the final contigs are:")
print(contigs, copies)