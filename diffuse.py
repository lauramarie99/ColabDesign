# Packages
import sys, random, string, re, os, time
if 'RFdiffusion' not in sys.path:
  os.environ["DGLBACKEND"] = "pytorch"
  sys.path.append('RFdiffusion')
from colabdesign.rf.utils import fix_contigs, fix_partial_contigs, fix_pdb, sym_it
from colabdesign.shared.protein import pdb_to_string
from rfdiffusion.inference.utils import parse_pdb
from IPython.display import display
import subprocess
import yaml
import argparse

# Run subprocess
def run(command, trigger, total_timesteps):
    #progress = widgets.FloatProgress(min=0, max=1, description='running', bar_style='info')
    #display(progress)
    pattern = re.compile(f'.*{trigger}.*')
    #progress_counter = 0
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
    while True:
        line = process.stdout.readline()
        if not line: break    
        #if pattern.match(line):
        #progress_counter += 1
        #progress.value = progress_counter / total_timesteps
    return_code = process.wait()
    #progress.description = "done"

# Run diffusion
def run_diffusion(contigs, name, path,
                  pdb=None, 
                  iterations=50,
                  symmetry="null", 
                  num_designs=10,
                  guide_scale=1,
                  guide_potentials="",
                  substrate="",
                  ckpt_override_path="null",
                  enzyme_design=True,
                  noise_scale=1):
    """
    This function runs a diffusion simulation using provided input parameters, 
    applies symmetry and contigs processing, and generates the final PDB structures.

    Args:
    contigs (str): Input contigs string to define the fixed and free portions.
    path (str): The output directory path for generated results.
    pdb (str, optional): The PDB file path. Defaults to None.
    iterations (int, optional): Number of diffusion iterations. Defaults to 50.
    symmetry (str, optional): Symmetry type ("null", "auto", "cyclic", "dihedral"). Defaults to "none".
    order (int, optional): Order for cyclic and dihedral symmetry. Defaults to 1.
    hotspot (str, optional): Hotspot residues for the protein-protein interaction site. Defaults to None.
    chains (str, optional): Chains to include in the simulation. Defaults to None.
    add_potential (bool, optional): If True, adds oligomer contact guiding potentials. Defaults to False.
    num_designs (int, optional): Number of designs to generate. Defaults to 5.
    guide_scale (float): Scaling factor for guiding potentials. Defaults to 20.
    guide_potentials (str): The guiding potentials string. Defaults to an empty string.
    substrate (str): The substrate design. Defaults to "2PE".
    ckpt_override_path (str): The path of the checkpoint file. Defaults to "./RFdiffusion/models/ActiveSite_ckpt.pt".
    enzyme_design (bool, optional): If True, performs enzyme design by adding guiding potentials. Defaults to True.
    noise_scale (int, optional): Change noise_scale_ca and noise_scale_frame
    
    Returns:
    tuple: The updated contigs list and the number of symmetry-equivalent copies.
    """

    # Make output directory
    full_path = f"{path}{name}/Diffusion"
    print(full_path)
    os.makedirs(full_path, exist_ok=True)
    output_prefix = f"{full_path}/{name}"

    # Add general options
    opts = [f"inference.output_prefix={output_prefix}", 
            f"inference.num_designs={num_designs}",
            f"denoiser.noise_scale_ca={noise_scale}",
            f"denoiser.noise_scale_frame={noise_scale}",
            f"inference.ckpt_override_path={ckpt_override_path}"]

    # Determine the mode based on the provided contigs input
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

    # Symmetry
    if symmetry != "null":
       raise Exception("Symmetry options are not implemented yet!")
    else:
       copies = 1
    
    # Process input contigs based on specified mode
    if mode == "fixed":
      
        # Get PDB string
        pdb_str = pdb_to_string(pdb, chains=fixed_chains)
        #print(f"pdb_str: {pdb_str}")
      
        # Get input PDB
        pdb_filename = f"{full_path}/input.pdb"
        os.system(f"cp {pdb} {pdb_filename}")

        # Parse the PDB file and update options
        parsed_pdb = parse_pdb(pdb_filename)
        opts.append(f"inference.input_pdb={pdb_filename}")

        # Process contigs and options for the fixed mode
        opts.append(f"diffuser.T={iterations}")
        # Print prefix contigs for diagnostic purposes
        print("prefix contigs:", contigs)
        contigs = fix_contigs(contigs, parsed_pdb)
        print("fixed contigs:", contigs)
    
    # Process contigs and options for the free mode
    elif mode == "free":
        opts.append(f"diffuser.T={iterations}")
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

    # Print different parameters for diagnostic purposes
    print("mode:", mode)
    print("output:", full_path)
    print("contigs:", contigs)

    # Create the command with options to run the inference script
    opts_str = " ".join(opts)
    cmd = f"python3.9 ./RFdiffusion/run_inference.py {opts_str}"
    print(cmd)

    # Run the command using a helper function "run"
    steps = (iterations - 1) * num_designs
    run(cmd, "Timestep", steps)

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





# Get config
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
contigs, copies = run_diffusion(**args_diffusion)

# Copy config to results directory
os.system(f"cp {config} {path}{name}/")

# Print output contigs
print("the final contigs are:")
print(contigs, copies)