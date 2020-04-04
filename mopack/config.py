import json
import os
import yaml

from .sources import make_package

mopack_dirname = 'mopack'
metadata_filename = 'mopack.json'


def accumulate_config(filename, config=None):
    if config is None:
        config = {'packages': {}}
    with open(filename) as f:
        next_config = yaml.safe_load(f)
        for v in next_config['packages'].values():
            v['_config_file'] = os.path.abspath(filename)
        config['packages'].update(next_config['packages'])
    return config


def finalize_config(config):
    result = {'packages': set()}
    for k, v in config['packages'].items():
        result['packages'].add(make_package(k, v))
    return result


def fetch(config, builddir):
    pkgdir = os.path.join(builddir, mopack_dirname)
    metadata = {}
    for i in config['packages']:
        x = i.fetch(pkgdir)
        metadata[i.name] = x
    with open(os.path.join(pkgdir, metadata_filename), 'w') as f:
        json.dump(metadata, f)


def get_metadata(builddir):
    pkgdir = os.path.join(builddir, mopack_dirname)
    with open(os.path.join(pkgdir, metadata_filename)) as f:
        return json.load(f)
