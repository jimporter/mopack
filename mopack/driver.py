import argparse
import os
import json

from . import commands, config, log
from .app_version import version

logger = log.getLogger(__name__)

# This environment variable is set to the top builddir when `mopack resolve` is
# executed so that nested invocations of `mopack` consistently point to the
# same mopack directory. XXX: There might be a smarter way to do this, but this
# should be ok for the time being at least...
nested_invoke = 'MOPACK_NESTED_INVOCATION'


class KeyValueAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        key, value = values.split('=', 1)
        if getattr(namespace, self.dest) is None:
            setattr(namespace, self.dest, {})
        getattr(namespace, self.dest)[key] = value


def resolve(parser, subparser, args):
    if os.environ.get(nested_invoke):
        return

    os.environ[nested_invoke] = os.path.abspath(args.directory)
    config_data = config.Config(args.file)
    commands.resolve(config_data, commands.get_package_dir(args.directory),
                     args.deploy_paths)


def info(parser, subparser, args):
    args.directory = os.environ.get(nested_invoke, args.directory)
    metadata = commands.Metadata.load(commands.get_package_dir(args.directory))
    print(json.dumps(metadata.packages[args.package]))


def deploy(parser, subparser, args):
    assert nested_invoke not in os.environ
    commands.deploy(commands.get_package_dir(args.directory))


def clean(parser, subparser, args):
    assert nested_invoke not in os.environ
    commands.clean(commands.get_package_dir(args.directory))


def main():
    parser = argparse.ArgumentParser(prog='mopack')
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + version)
    parser.add_argument('--debug', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--color', metavar='WHEN',
                        choices=['always', 'never', 'auto'], default='auto',
                        help=('show colored output (one of: %(choices)s; ' +
                              'default: %(default)s)'))
    parser.add_argument('-c', action='store_const', const='always',
                        dest='color',
                        help=('show colored output (equivalent to ' +
                              '`--color=always`)'))
    parser.add_argument('--warn-once', action='store_true',
                        help='only emit a given warning once')

    subparsers = parser.add_subparsers(metavar='COMMAND')

    resolve_p = subparsers.add_parser(
        'resolve', help='fetch and build package dependencies'
    )
    resolve_p.set_defaults(func=resolve, parser=resolve_p)
    resolve_p.add_argument('--directory', default='.', metavar='PATH',
                           help='directory to store local package data in')
    resolve_p.add_argument('-P', '--deploy-path', action=KeyValueAction,
                           dest='deploy_paths', metavar='TYPE=PATH',
                           help='directories to deploy packages to')
    resolve_p.add_argument('file', nargs='+',
                           help='the mopack configuration files')

    info_p = subparsers.add_parser(
        'info', help='retrieve info about a package'
    )
    info_p.set_defaults(func=info, parser=info_p)
    info_p.add_argument('--directory', default='.', metavar='PATH',
                        help='directory storing local package data')
    info_p.add_argument('package', help='the name of the package to query')

    deploy_p = subparsers.add_parser(
        'deploy', help='deploy packages'
    )
    deploy_p.set_defaults(func=deploy, parser=deploy_p)
    deploy_p.add_argument('--directory', default='.', metavar='PATH',
                          help='directory storing local package data')

    clean_p = subparsers.add_parser(
        'clean', help='clean package directory'
    )
    clean_p.set_defaults(func=clean, parser=clean_p)
    clean_p.add_argument('--directory', default='.', metavar='PATH',
                         help='directory storing local package data')

    args = parser.parse_args()
    log.init(args.color, debug=args.debug, warn_once=args.warn_once)

    try:
        return args.func(parser, args.parser, args)
    except Exception as e:
        logger.exception(e)
        return 1
