# Packages
import subprocess, glob, time, os, argparse

# Create a slurm script
def create_slurm_script(colabdesign_path, slurm_path, container, config, script, 
                        outdir, name, jobname, time='24:00:00', mem='10000', cpus=1, 
                        gpu='a30:1', partition='paula', email='', emailType='FAIL', 
                        excludeNodes='', dependency=''):
    with open(f'{slurm_path}/{name}.slurm', 'w') as slurmFile:
        slurmFile.writelines([
                "#!/bin/bash\n",
                f"#SBATCH --job-name={jobname}\n",
                f"#SBATCH --output={outdir}/{name}.out\n",
                f"#SBATCH --error={outdir}/{name}.err\n",
                f"#SBATCH --time={time}\n",
                f"#SBATCH --mem={mem}\n",
                f"#SBATCH --cpus-per-task={cpus}\n",
                f"#SBATCH --gres=gpu:{gpu}\n",
                f"#SBATCH --partition={partition}\n",
                f"#SBATCH --mail-user={email}\n",
                f"#SBATCH --mail-type={emailType}\n",
                f"#SBATCH --exclude={excludeNodes}\n"
        ])
        if len(dependency) > 0:
            slurmFile.writelines([
                f"#SBATCH --dependency=afterok:{dependency}\n"
            ])
        slurmFile.writelines([
                '# define CONTAINER\n',
                f'CONTAINER={container}\n',
                '# define SCRIPT or program to call inside the container\n',
                f'SCRIPT="{script} --config {config}"\n',
                f'cd {colabdesign_path}\n',
                'singularity exec --nv --cleanenv $CONTAINER $SCRIPT\n'      
        ])

# Run single slurm script, returns job id and error message
def run_slurm_script(name, cwd):
    slurm_command = f'/usr/bin/sbatch {name}.slurm'
    process = subprocess.Popen(slurm_command,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True,
                               shell=True,
                               cwd=cwd)
    output, error = process.communicate()
    if error == '':
        output = output.split()[-1]
    return output, error

# Run all slurm scripts, returns dictionary with job ids and dictionary with error messages
def run_all_slurm_scripts(slurm_path):
    slurm_files = glob.glob(
        f'{slurm_path}/*.slurm')
    job_ids = {}
    errors = {}
    for slurm_file in slurm_files:
        name = slurm_file.split('/')[-1].split('.')[0]
        output, error = run_slurm_script(name=name, cwd=slurm_path)
        job_ids[name] = output
        errors[name] = error
    return job_ids, errors

# Check if job is already done, returns True/False
def check_if_job_is_done(job_id):
    time.sleep(1)
    slurm_command = f'/usr/bin/squeue -j {job_id}'
    process = subprocess.Popen(slurm_command,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True,
                               shell=True)
    output, error = process.communicate()
    if job_id in output:
        return False
    return True

# Check if diffusion was successfull, returns True/False
def check_if_diffusion_done(name, slurm_path):
    if not os.path.exists(f"{slurm_path}/Diffusion/{name}.out"):
        return False
    with open(f"{slurm_path}/Diffusion/{name}.out") as myfile:
        if "the final contigs are" in myfile.read():
            return True
        return False

# Check if validation was successful, returns True/False
def check_if_validation_done(name,slurm_path):
    if not os.path.exists(f"{slurm_path}/Validation/{name}.out"):
        return False
    with open(f"{slurm_path}/Validation/{name}.out") as myfile:
        if "running designability" in myfile.read():
            return True
        return False

# Check if GPU is used during diffusion, returns Ture/False
def check_if_gpu_used(name, slurm_path):
    if not os.path.exists(f"{slurm_path}/Diffusion/{name}.err"):
        return False
    with open(f"{slurm_path}/Diffusion/{name}.err") as myfile:
        if "CUDA unknown error" in myfile.read():
            return False
        return True

# Cancel job, returns output and error message
def cancel_job(job_id):
    slurm_command = f'/usr/bin/scancel {job_id}'
    process = subprocess.Popen(slurm_command,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               universal_newlines=True,
                               shell=True)
    output, error = process.communicate()
    return output, error

# Resubmit job, returns output and error message
def resubmit_job(name,job_id,slurm_path):
    cancel_job(job_id)
    output, error = run_slurm_script(name=name,cwd=slurm_path)
    return output, error
    
# Start diffusion jobs, returns dictionary with job ids and dictionary with error messages   
def run_diffusion(colabdesign_path, config_path, slurm_path, container, diffusion_path):
    config_files = glob.glob(
        f'{config_path}/*.yml')
    for config_file in config_files:
        name = config_file.split('/')[-1].split('.')[0]
        create_slurm_script(colabdesign_path=colabdesign_path, slurm_path=slurm_path, container=container,
                            config=config_file, script=diffusion_path, outdir=slurm_path,name=f"{name}_diffusion",
                            jobname=f"diff-{name}", time="01:00:00", mem="10000", cpus=1, gpu="a30:1", 
                            partition="paula",email="", emailType="FAIL", excludeNodes='')
    job_ids, errors = run_all_slurm_scripts(slurm_path=slurm_path)
    return job_ids, errors


# Start validation job if diffusion is done, returns dictionary with job ids and dictionary with error messages 
def run_validation(colabdesign_path, config_path, slurm_path, diffusion_job_ids, container, validation_path):
    validation_job_ids = {}
    validation_errors = {}
    for name,job_id in diffusion_job_ids.items():
        counter = 0
        new_job_id = job_id
        exp_name = name[:-10]
        config_file = f"{config_path}/{exp_name}.yml"
        slurm_name = f"{exp_name}_validation"
        create_slurm_script(colabdesign_path=colabdesign_path, slurm_path=slurm_path, container=container,
                            config=config_file, script=validation_path, outdir=slurm_path, name=slurm_name,
                            jobname=f"val-{exp_name}", time="01:00:00", mem="10000", cpus=1, gpu="a30:1",
                            partition="paula", email="", emailType="FAIL", excludeNodes="", dependency=job_id)
    validation_job_ids, errors = run_all_slurm_scripts(slurm_path=slurm_path)
    return validation_job_ids, validation_errors


"""
MAIN
"""

# Global variables
argParser = argparse.ArgumentParser()
argParser.add_argument('-r','--run')                                                                    # Name of run
args = argParser.parse_args()

# Adapt paths!
diffusion_container = "/home/proteindesign.sif"                                                         # Location diffusion container
validation_container = "/home/colabdesign1.1.0.sif"                                                     # Location validation container
config_path = f"/home/{args.run}/Configs"                                                               # Location config files
slurm_path = f"/home/{args.run}/Slurm"                                                                  # Location slurm files
colabdesign_path = "/home/Colabdesign"                                                                  # Location colabdesign repository
diffusion_path = "python3.9 diffuse.py"                                                                 # Call diffuse.py 
validation_path = "python3 validate.py"                                                                 # Call validate.py

# Run diffusion and validation
if not os.path.exists(f"{slurm_path}/Diffusion"):
   os.makedirs(f"{slurm_path}/Diffusion")
   os.makedirs(f"{slurm_path}/Validation")
diffusion_job_ids, diffusion_errors = run_diffusion(colabdesign_path=colabdesign_path, 
                                                    config_path=config_path,
                                                    slurm_path=f"{slurm_path}/Diffusion",
                                                    container=diffusion_container,
                                                    diffusion_path=diffusion_path)
print("Diffusion jobs submitted")

validation_job_ids, validation_errors = run_validation(colabdesign_path=colabdesign_path,
                                                       config_path=config_path,
                                                       slurm_path=f"{slurm_path}/Validation",
                                                       diffusion_job_ids=diffusion_job_ids,
                                                       container=validation_container,
                                                       validation_path=validation_path)
print("Validation jobs submitted")

# Check if validation successful
for name,job_id in validation_job_ids.items():
    while not check_if_job_is_done(job_id=job_id):
        time.sleep(30)
    exp_name = name[:-11]
    if check_if_validation_done(name,slurm_path):
        print("Validation done:", exp_name)
    else:
        print("Validation failed:", exp_name)