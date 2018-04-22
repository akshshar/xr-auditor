#/usr/bin/env.python
import yaml
import pdb

def yaml_to_dict(yaml_file):
        yaml_dict = {}
        try:
            with open(yaml_file, 'r') as stream:
                try:
                    yaml_dict = yaml.load(stream)
                except yaml.YAMLError as e:
                    print("Failed to parse YAML file, Error: %s" % e)
        except Exception as e:
            print("Failed to open compliance config YAML file")
            print("Error is %s" % e)

        return yaml_dict


print yaml_to_dict("server.cfg.yml")
pdb.set_trace()
