import argparse
import os
import json

from . import config

# This environment variable is set to the top builddir when `mopack resolve` is
# executed so that nested invocations of `mopack` consistently point to the
# same mopack directory. XXX: There might be a smarter way to do this, but this
# should be ok for the time being at least...
nested_invoke = 'MOPACK_NESTED_INVOCATION'


def resolve(parser, subparser, args):
    if os.environ.get(nested_invoke):
        return

    os.environ[nested_invoke] = os.path.abspath(args.directory)
    config_data = config.Config(args.file)
    config.resolve(config_data, config.get_package_dir(args.directory))


def info(parser, subparser, args):
    args.directory = os.environ.get(nested_invoke, args.directory)
    metadata = config.get_metadata(config.get_package_dir(args.directory))
    print(json.dumps(metadata[args.package]))


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(metavar='COMMAND')

    resolve_p = subparsers.add_parser(
        'resolve', help='fetch and build package dependencies'
    )
    resolve_p.set_defaults(func=resolve, parser=resolve_p)
    resolve_p.add_argument('--directory', default='.')
    resolve_p.add_argument('file', nargs='+')

    info_p = subparsers.add_parser(
        'info', help='retrieve info about a package'
    )
    info_p.set_defaults(func=info, parser=info_p)
    info_p.add_argument('--directory', default='.')
    info_p.add_argument('package')

    args = parser.parse_args()
    return args.func(parser, args.parser, args)
