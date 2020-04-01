import json
import os
import yaml

from .path import pushd
from .sources import make_package

metadata_file = 'mopack.json'


def accumulate_config(filename, config=None):
    if config is None:
        config = {'packages': {}}
    with open(filename) as f:
        next_config = yaml.safe_load(f)
        config['packages'].update(next_config['packages'])
    return config


def finalize_config(config):
    result = {'packages': set()}
    for k, v in config['packages'].items():
        result['packages'].add(make_package(k, v))
    return result


def fetch(config, directory):
    info = {}
    with pushd(directory, makedirs=True, exist_ok=True):
        for i in config['packages']:
            x = i.fetch()
            info[i.name] = x
        with open(metadata_file, 'w') as f:
            json.dump(info, f)


def get_metadata(directory):
    with open(os.path.join(directory, metadata_file)) as f:
        return json.load(f)
