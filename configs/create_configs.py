# Packages
import random
import argparse
import yaml
import os

# Get config
parser = argparse.ArgumentParser()
parser.add_argument('--config', type=str, required=True)
args = parser.parse_args()
args = yaml.safe_load(open(args.config))
args_general = args['general']
args_diffusion = args['diffusion']
args_validation = args['validation']
setups = ["A","B","C","D","E","F","G","H","I","J"]

# Read config file
name = args_general['name']
contig = args_general['contigs']
num_contigs = args_general['num_contigs']
noise_scale = args_general['noise_scale']
guide_scale = args_general['guide_scale']
recycles = args_general['num_recycles']
configdir = args_general['configdir']
resultsdir = args_general['resultsdir']
yaml_dict = {}
if not os.path.exists(configdir):
   os.makedirs(configdir)

# Create random contig
for n in range(num_contigs):
    new_contig_sections = []
    sections = contig.split("/")
    for section in sections:
        if section[0].isalpha():
            new_contig_sections.append(section)
            continue
        lb = int(section.split('-')[0])
        ub = int(section.split('-')[1])
        if lb != ub:
            random_number = random.randint(lb,ub)
            new_contig_sections.append(str(random_number) + "-" + str(random_number))
        else:
            new_contig_sections.append(str(lb) + "-" + str(lb))
    new_contig = '/'.join(new_contig_sections)
    counter = 0
    # Make config for each value in noise scale list and guide scale list
    if args_diffusion['enzyme_design']:
        for noise in noise_scale:
            for scale in guide_scale:
                for recycle in recycles:
                    config_name = name + '_' + str(n) + '_' + setups[counter]
                    yaml_dict['diffusion'] = args_diffusion
                    yaml_dict['diffusion']['name'] = config_name
                    yaml_dict['diffusion']['path'] = resultsdir
                    yaml_dict['diffusion']['contigs'] = new_contig
                    yaml_dict['diffusion']['guide_scale'] = scale
                    yaml_dict['diffusion']['noise_scale'] = noise
                    yaml_dict['validation'] = args_validation
                    yaml_dict['validation']['num_recycles'] = recycle

                    file = open(configdir + config_name + ".yml","w")
                    yaml.dump(yaml_dict,file)
                    file.close()
                    counter += 1
    
    else:
        for noise in noise_scale:
            for recycle in recycles:
                config_name = name + '_' + str(n) + '_' + setups[counter]
                yaml_dict['diffusion'] = args_diffusion
                yaml_dict['diffusion']['name'] = config_name
                yaml_dict['diffusion']['path'] = resultsdir
                yaml_dict['diffusion']['contigs'] = new_contig
                yaml_dict['diffusion']['noise_scale'] = noise 
                yaml_dict['validation'] = args_validation
                yaml_dict['validation']['num_recycles'] = recycle

                file = open(configdir + config_name + ".yml","w")
                yaml.dump(yaml_dict,file)
                file.close()
                counter += 1

        

        



