import argparse
import json

from . import config


def fetch(parser, subparser, args):
    config_data = None
    for i in args.file:
        config_data = config.accumulate_config(i, config_data)
    config_data = config.finalize_config(config_data)

    config.fetch(config_data, args.directory)


def info(parser, subparser, args):
    metadata = config.get_metadata(args.directory)
    print(json.dumps(metadata[args.package]))


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(metavar='COMMAND')

    fetch_p = subparsers.add_parser(
        'fetch', help='fetch and build package dependencies'
    )
    fetch_p.set_defaults(func=fetch, parser=fetch_p)
    fetch_p.add_argument('--directory', default='mopack')
    fetch_p.add_argument('file', nargs='+')

    info_p = subparsers.add_parser(
        'info', help='retrieve info about a package'
    )
    info_p.set_defaults(func=info, parser=info_p)
    info_p.add_argument('--directory', default='mopack')
    info_p.add_argument('package')

    args = parser.parse_args()
    return args.func(parser, args.parser, args)
