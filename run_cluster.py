
import subprocess, glob, time

# Create a slurm script
def create_slurm_script(slurm_path, container, config, script, outdir, name, jobname, time='24:00:00', mem='10000', 
                        cpus=1, gpu='a30:1', partition='paula', email='zo23uqar@studserv.uni-leipzig.de', emailType='FAIL'):
    with open(f'{slurm_path}{name}.slurm', 'w') as slurmFile:
        slurmFile.writelines([
                "#!/bin/bash\n",
                f"#SBATCH --job-name={jobname}\n",
                f"#SBATCH --output={outdir}{name}.out\n",
                f"#SBATCH --error={outdir}{name}.err\n",
                f"#SBATCH --time={time}\n",
                f"#SBATCH --mem={mem}\n",
                f"#SBATCH --cpus-per-task={cpus}\n",
                f"#SBATCH --gres=gpu:{gpu}\n",
                f"#SBATCH --partition={partition}\n",
                f"#SBATCH --mail-user={email}\n",
                f"#SBATCH --mail-type={emailType}\n",
                f"#SBATCH --partition={partition}\n"
        ])
        slurmFile.writelines([
                '# define CONTAINER\n',
                f'CONTAINER={container}\n',
                '# define SCRIPT or program to call inside the container\n',
                f'SCRIPT="{script} --config {config}"\n',
                'singularity exec --nv --cleanenv $CONTAINER $SCRIPT\n'      
        ])


# Run single slurm script
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


# Run all slurm scripts
def run_all_slurm_scripts(slurm_path):
    slurm_files = glob.glob(
        f'{slurm_path}/*.slurm')
    job_ids = []
    errors = []

    for slurm_file in slurm_files:
        name = slurm_file.split('/')[-1].split('.')[0]
        output, error = run_slurm_script(
            name=name,
            cwd=slurm_path)
        job_ids[name] = output
        errors[name] = error

    return job_ids, errors


# Check if job is already done
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
        else:
            return True


# Start diffusion jobs     
def run_diffusion(config_path, slurm_path, container):
    config_files = glob.glob(
        f'{config_path}/*.yml')
    for config_file in config_files:
        name = config_file.split('/')[-1].split('.')[0]
        create_slurm_script(slurm_path=slurm_path,container=container,config=config_file,script="python3.9 /home/sc.uni-leipzig.de//ProteinDesign/ColabDesign/diffuse.py",
                            outdir=slurm_path,name=f"{name}_diffusion",jobname=f"diffusion-{name}", time="24:00:00", mem="10000", cpus=1,
                            gpu="a30:1",partition="paula",email="zo23uqar@studserv.uni-leipzig.de",emailType="FAIL")
    job_ids, errors = run_all_slurm_scripts(slurm_path=slurm_path)
    return job_ids, errors


# Start validation job if diffusion is done
def run_validation(config_path, slurm_path, diffusion_job_ids, container):
    validation_job_ids = []
    validation_errors = []
    for name,job_id in diffusion_job_ids.items():
        while not check_if_job_is_done(job_id=job_id):
            time.sleep(30)
        exp_name = name.split("_")[0]
        print("Diffusion done:", exp_name)
        config_file = f"{config_path}{exp_name}.yml"
        slurm_name = f"{exp_name}_validation"
        create_slurm_script(slurm_path=slurm_path,container=container,config=config_file,script="python3.9 /home/sc.uni-leipzig.de//ProteinDesign/ColabDesign/validate.py",
                            outdir=slurm_path,name=slurm_name,jobname=f"validation-{exp_name}", time="24:00:00", mem="10000", cpus=1,
                            gpu="",partition="clara",email="zo23uqar@studserv.uni-leipzig.de",emailType="FAIL")
        output, error = run_slurm_script(name=slurm_name, cwd=slurm_path)
        validation_errors[slurm_name] = error
        if error == '':
            validation_job_ids[slurm_name] = output
            print("Validation started:", exp_name)
    return validation_job_ids, validation_errors


"""
MAIN
"""

# Global variables
# diffusion_container = "/home/sc.uni-leipzig.de//ProteinDesign/"
# validation_container = "/home/sc.uni-leipzig.de//ProteinDesign/"
# config_path = "/home/sc.uni-leipzig.de//ProteinDesign/Diffusion/Run1/In/Configs/"
# slurm_path = "/home/sc.uni-leipzig.de//ProteinDesign/Diffusion/Run1/In/Slurm/"


# # Run diffusion and validation
# diffusion_job_ids, diffusion_errors = run_diffusion(config_path=config_path,slurm_path=f"{slurm_path}Diffusion",container=diffusion_container)
# print("Diffusion jobs submitted")
# print("Errors:", diffusion_errors)
# validation_job_ids, validation_errors = run_validation(config_path=config_path,slurm_path=f"{slurm_path}Validation",diffusion_job_ids=diffusion_job_ids,container=validation_container)
# print("Validation jobs submitted")
# print("Errors:", validation_errors)
# for name,job_id in validation_job_ids.items():
#     while not check_if_job_is_done(job_id=job_id):
#         time.sleep(30)
#     exp_name = name.split("_")[0]
#     print("Validation done:", exp_name)
    
