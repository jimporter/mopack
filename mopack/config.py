import json
import os
import yaml

from .sources import make_package

mopack_dirname = 'mopack'
metadata_filename = 'mopack.json'


def accumulate_config(filename, config=None):
    if config is None:
        config = {'packages': {}}

    filename = os.path.abspath(filename)
    with open(filename) as f:
        next_config = yaml.safe_load(f)
        for v in next_config['packages'].values():
            v['_config_file'] = filename
        config['packages'].update(next_config['packages'])

    return config


def finalize_config(config):
    result = {'packages': []}
    for k, v in config['packages'].items():
        result['packages'].append(make_package(k, v))
    return result


def fetch(config, builddir):
    pkgdir = os.path.join(builddir, mopack_dirname)
    metadata, pending = {}, {}
    for i in config['packages']:
        if hasattr(i, 'fetch_all'):
            pending.setdefault(type(i), []).append(i)
        else:
            metadata[i.name] = i.fetch(pkgdir)

    for k, v in pending.items():
        metadata.update(k.fetch_all(pkgdir, v))

    with open(os.path.join(pkgdir, metadata_filename), 'w') as f:
        json.dump(metadata, f)


def get_metadata(builddir):
    pkgdir = os.path.join(builddir, mopack_dirname)
    with open(os.path.join(pkgdir, metadata_filename)) as f:
        return json.load(f)
