import sys, random, string, re, os
if 'RFdiffusion' not in sys.path:
  os.environ["DGLBACKEND"] = "pytorch"
  sys.path.append('RFdiffusion')


from colabdesign.rf.utils import fix_contigs, fix_partial_contigs, fix_pdb, sym_it
import json
import numpy as np
from colabdesign.shared.protein import pdb_to_string
from rfdiffusion.inference.utils import parse_pdb

from IPython.display import display
#/root/micromamba/envs/SE3nv/bin/python -m pip install ipywidgets -t ./local
#from local import ipywidgets as widgets
import subprocess



def get_pdb(pdb_code=None):
  if pdb_code is None or pdb_code == "":
    upload_dict = files.upload()
    pdb_string = upload_dict[list(upload_dict.keys())[0]]
    with open("tmp.pdb","wb") as out: out.write(pdb_string)
    return "tmp.pdb"
  elif os.path.isfile(pdb_code):
    return pdb_code
  elif len(pdb_code) == 4:
    if not os.path.isfile(f"{pdb_code}.pdb1"):
      os.system(f"wget -qnc https://files.rcsb.org/download/{pdb_code}.pdb1.gz")
      os.system(f"gunzip {pdb_code}.pdb1.gz")
    return f"{pdb_code}.pdb1"
  else:
    os.system(f"wget -qnc https://alphafold.ebi.ac.uk/files/AF-{pdb_code}-F1-model_v3.pdb")
    return f"AF-{pdb_code}-F1-model_v3.pdb"

def run_ananas(pdb_str, path, sym=None):
  pdb_filename = f"outputs/{path}/ananas_input.pdb"
  out_filename = f"outputs/{path}/ananas.json"
  with open(pdb_filename,"w") as handle:
    handle.write(pdb_str)  
  
  cmd = f"./ananas {pdb_filename} -u -j {out_filename}"
  if sym is None: os.system(cmd)
  else: os.system(f"{cmd} {sym}")
  
  # parse results
  try:
    out = json.loads(open(out_filename,"r").read())
    results,AU = out[0], out[-1]["AU"]
    group = AU["group"]
    chains = AU["chain names"]
    rmsd = results["Average_RMSD"]
    print(f"AnAnaS detected {group} symmetry at RMSD:{rmsd:.3}")

    C = np.array(results['transforms'][0]['CENTER'])
    A = [np.array(t["AXIS"]) for t in results['transforms']]

    # apply symmetry and filter to the asymmetric unit
    new_lines = []
    for line in pdb_str.split("\n"):
      if line.startswith("ATOM"):
        chain = line[21:22]
        if chain in chains:
          x = np.array([float(line[i:(i+8)]) for i in [30,38,46]])
          if group[0] == "c":
            x = sym_it(x,C,A[0])
          if group[0] == "d":
            x = sym_it(x,C,A[1],A[0])
          coord_str = "".join(["{:8.3f}".format(a) for a in x])
          new_lines.append(line[:30]+coord_str+line[54:])
      else:
        new_lines.append(line)
    return results, "\n".join(new_lines)  
  
  except:
    return None, pdb_str

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

def run_diffusion(contigs, path, 
                  pdb=None, 
                  iterations=50,
                  symmetry="none", 
                  order=1, 
                  hotspot=None,
                  chains=None, 
                  add_potential=False,
                  num_designs=5,
                  guide_scale=20,
                  guide_potentials="",
                  substrate="2PE",
                  ckpt_override_path="./RFdiffusion/models/ActiveSite_ckpt.pt",
                  enzyme_design=True,):
  """
    This function runs a diffusion simulation using provided input parameters, 
    applies symmetry and contigs processing, and generates the final PDB structures.

    Args:
    contigs (str): Input contigs string to define the fixed and free portions.
    path (str): The output directory path for generated results.
    pdb (str, optional): The PDB file path. Defaults to None.
    iterations (int, optional): Number of diffusion iterations. Defaults to 50.
    symmetry (str, optional): Symmetry type ("none", "auto", "cyclic", "dihedral"). Defaults to "none".
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

    Returns:
    tuple: The updated contigs list and the number of symmetry-equivalent copies.
  """
  full_path = f"outputs/{path}"
  os.makedirs(full_path, exist_ok=True)
  opts = [f"inference.output_prefix={full_path}", 
          f"inference.num_designs={num_designs}"]

  if chains == "": chains = None

  # determine symmetry type
  if symmetry in ["auto","cyclic","dihedral"]:
    if symmetry == "auto":
      sym, copies = None, 1
    else:
      sym, copies = {"cyclic":(f"c{order}",order),
                     "dihedral":(f"d{order}",order*2)}[symmetry]
  else:
    symmetry = None
    sym, copies = None, 1

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


  # Process input contigs based on specified mode and symmetry
  if mode in ["partial", "fixed"]:
      
      # Convert the PDB structure to a string
      pdb_str = pdb_to_string(get_pdb(pdb), chains=chains)

      # Automatic symmetry detection and processing
      if symmetry == "auto":
          a, pdb_str = run_ananas(pdb_str, path)
          if a is None:
              print('ERROR: no symmetry detected')
              symmetry, sym, copies = None, None, 1
          else:
              if a["group"][0] == "c":
                  symmetry = "cyclic"
                  sym, copies = a["group"], int(a["group"][1:])
              elif a["group"][0] == "d":
                  symmetry = "dihedral"
                  sym, copies = a["group"], 2 * int(a["group"][1:])
              else:
                  print(f'ERROR: the detected symmetry ({a["group"]}) not currently supported')
                  symmetry, sym, copies = None, None, 1

      # Update PDB string for fixed mode
      elif mode == "fixed":
          pdb_str = pdb_to_string(pdb_str, chains=fixed_chains)
      print(f"pdb_str: {pdb_str}")
      # Write the PDB file
      pdb_filename = f"{full_path}/input.pdb"
      with open(pdb_filename, "w") as handle:
          handle.write(pdb_str)

      # Parse the PDB file and update options
      parsed_pdb = parse_pdb(pdb_filename)
      opts.append(f"inference.input_pdb={pdb_filename}")

      # Process contigs and options for the partial mode
      if mode == "partial":
          iterations = int(80 * (iterations / 200))
          opts.append(f"diffuser.partial_T={iterations}")
          contigs = fix_partial_contigs(contigs, parsed_pdb)

      # Process contigs and options for the fixed mode
      else:
          opts.append(f"diffuser.T={iterations}")
          # Print prefix contigs for diagnostic purposes
          print("prefix contigs:", contigs)
          contigs = fix_contigs(contigs, parsed_pdb)
          print("fixed contigs:", contigs)
  # Process contigs and options for the free mode
  else:
      opts.append(f"diffuser.T={iterations}")
      parsed_pdb = None
      contigs = fix_contigs(contigs, parsed_pdb)

  # Add hotspot residues option, if provided
  if hotspot is not None and hotspot != "":
      opts.append(f"ppi.hotspot_res=[{hotspot}]")


  # Setup symmetry information for processing
  if sym is not None:
      sym_opts = ["--config-name symmetry", f"inference.symmetry={sym}"]

      if add_potential:
          sym_opts += [
              "'potentials.guiding_potentials=[\"type:olig_contacts,weight_intra:1,weight_inter:0.1\"]'",
              "potentials.olig_intra_all=True",
              "potentials.olig_inter_all=True",
              "potentials.guide_scale=2",
              "potentials.guide_decay=quadratic"]

      opts = sym_opts + opts
      contigs = sum([contigs] * copies, [])

  opts.append(f"'contigmap.contigs=[{' '.join(contigs)}]'")

  # Add enzyme_design related options if enzyme_design is True
  if enzyme_design:
      opts.append(f"potentials.guide_scale={guide_scale}")
      opts.append(f"'potentials.guiding_potentials=[\"{guide_potentials}\"]'")
      opts.append(f"potentials.substrate={substrate}")
      opts.append(f"inference.ckpt_override_path={ckpt_override_path}")
      opts.append(f"denoiser.noise_scale_ca=0")

  # Print different parameters for diagnostic purposes
  print("mode:", mode)
  print("output:", full_path)
  print("contigs:", contigs)

  # Create the command with options to run the inference script
  opts_str = " ".join(opts)
  cmd = f"/root/micromamba/envs/SE3nv/bin/python ./RFdiffusion/run_inference.py {opts_str}"
  print(cmd)

  # Run the command using a helper function "run"
  steps = (iterations - 1) * num_designs
  run(cmd, "Timestep", steps)

  # Post-processing: fix PDB structures based on contigs
  for n in range(num_designs):
      pdbs = [
          f"outputs/traj/{path}_{n}_pX0_traj.pdb",
          f"outputs/traj/{path}_{n}_Xt-1_traj.pdb",
          f"{full_path}_{n}.pdb"]

      for pdb in pdbs:
          with open(pdb, "r") as handle:
              pdb_str = handle.read()

          with open(pdb, "w") as handle:
              handle.write(fix_pdb(pdb_str, contigs))

  return contigs, copies





#../scripts/run_inference.py inference.output_prefix=catalytic_triad/experiment0 \
#                            inference.input_pdb=input_pdbs/7nei_L210T_2pet_15337.pdb \
#                            'contigmap.contigs=[10-50/A130-130/10-50/A176-176/10-50/A208-208/10-50]' \
#                            potentials.guide_scale=1 \
#                            'potentials.guiding_potentials=["type:substrate_contacts,s:1,r_0:8,rep_r_0:5.0,rep_s:2,rep_r_min:1"]' \
#                            potentials.substrate=2PE \
#                            inference.ckpt_override_path=../models/ActiveSite_ckpt.pt



#@title run **RFdiffusion** to generate a backbone
name = "2PET-DiffuseAndDesignTest03_Noise0" #@param {type:"string"}
contigs = "10-50/A130-130/10-50/A176-176/10-50/A208-208/10-50" #@param {type:"string"}
pdb = "input_pdbs/7nei_L210T_2pet_15337.pdb" #@param {type:"string"}
iterations = 25 #@param ["25", "50", "100", "150", "200"] {type:"raw"}
hotspot = "" #@param {type:"string"}
num_designs = 1 #@param ["1", "2", "4", "8", "16", "32"] {type:"raw"}
guide_scale = 20 #@param ["0.5", "1", "2", "4"] {type:"raw"}
guide_potentials = "type:substrate_contacts,s:1,r_0:8,rep_r_0:5.0,rep_s:2,rep_r_min:1" #@param {type:"string"}
substrate = "2PE" #@param {type:"string"}
ckpt_override_path = "./RFdiffusion/models/ActiveSite_ckpt.pt" #@param {type:"string"}
enzyme_design = True #@param {type:"boolean"}

#@markdown **symmetry** settings

symmetry = "none" #@param ["none", "auto", "cyclic", "dihedral"]
order = 1 #@param ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"] {type:"raw"}
chains = "" #@param {type:"string"}
add_potential = True #@param {type:"boolean"}

# validate settings
num_seqs = 8 #@param ["1", "2", "4", "8", "16", "32", "64"] {type:"raw"}
initial_guess = False #@param {type:"boolean"}
num_recycles = 1 #@param ["0", "1", "2", "3", "6", "12"] {type:"raw"}
use_multimer = False #@param {type:"boolean"}
rm_aa = "C" #@param {type:"string"}
#@markdown - for **binder** design, we recommend `initial_guess=True num_recycles=3`

# determine where to save
path = name
while os.path.exists(f"outputs/{path}_0.pdb"):
  path = name + "_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))

flags = {"contigs":contigs,
         "pdb":pdb,
         "order":order,
         "iterations":iterations,
         "symmetry":symmetry,
         "hotspot":hotspot,
         "path":path,
         "chains":chains,
         "add_potential":add_potential,
         "num_designs":num_designs,
         "guide_scale":guide_scale,
         "guide_potentials":guide_potentials,
         "substrate":substrate,
         "ckpt_override_path":ckpt_override_path,
         "enzyme_design":enzyme_design
         }

for k,v in flags.items():
  if isinstance(v,str):
    flags[k] = v.replace("'","").replace('"','')

contigs, copies = run_diffusion(**flags)

# Print the output contigs
print("the final contigs are:")
print(contigs)

if not os.path.isfile("params/done.txt"):
  print("downloading AlphaFold params...")
  while not os.path.isfile("params/done.txt"):
    time.sleep(5)



contigs_str = ":".join(contigs)
opts = [f"--pdb=outputs/{path}_0.pdb",
        f"--loc=outputs/{path}",
        f"--contig={contigs_str}",
        f"--copies={copies}",
        f"--num_seqs={num_seqs}",
        f"--num_recycles={num_recycles}",
        f"--rm_aa={rm_aa}",
        f"--num_designs={num_designs}"]
if initial_guess: opts.append("--initial_guess")
if use_multimer: opts.append("--use_multimer")
opts = ' '.join(opts)

# Run using os.system
print("running designability...")
print(f"python ./designability_test.py {opts}")
os.system(f"/root/micromamba/envs/SE3nv/bin/python ./designability_test.py {opts}")