import argparse
import os
import json
import yaml

from . import commands, config, log, yaml_tools
from .app_version import version
from .iterutils import merge_into_dict

logger = log.getLogger(__name__)

# This environment variable is set to the top builddir when `mopack resolve` is
# executed so that nested invocations of `mopack` consistently point to the
# same mopack directory.
nested_invoke = 'MOPACK_NESTED_INVOCATION'

description = """
mopack ("multiple-origin packager
"""


class KeyValueAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        try:
            key, value = values.split('=', 1)
        except ValueError:
            raise argparse.ArgumentError(self, 'expected TYPE=PATH')
        if getattr(namespace, self.dest) is None:
            setattr(namespace, self.dest, {})
        getattr(namespace, self.dest)[key] = value


class ConfigOptionAction(argparse.Action):
    def __init__(self, *args, key=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.key = key or []

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            key, value = values.split('=', 1)
        except ValueError:
            raise argparse.ArgumentError(self, 'expected OPTION=VALUE')

        key = self.key + key.split(':')

        try:
            value = yaml.safe_load(value)
        except yaml.parser.ParserError:
            raise argparse.ArgumentError(
                self, 'invalid yaml: {!r}'.format(value)
            )
        for i in reversed(key):
            value = {i: value}

        if getattr(namespace, self.dest) is None:
            setattr(namespace, self.dest, {})
        merge_into_dict(getattr(namespace, self.dest), value)


def resolve(parser, subparser, args):
    if os.environ.get(nested_invoke):
        return 3

    config_data = config.Config(args.file, args.options, args.deploy_paths)
    os.environ[nested_invoke] = args.directory
    commands.resolve(config_data, commands.get_package_dir(args.directory))


def usage(parser, subparser, args):
    directory = os.environ.get(nested_invoke, args.directory)
    usage = commands.usage(commands.get_package_dir(directory),
                           args.package, args.submodules, args.strict)

    if args.json:
        print(json.dumps(usage))
    else:
        print(yaml_tools.dump(usage))


def deploy(parser, subparser, args):
    assert nested_invoke not in os.environ
    commands.deploy(commands.get_package_dir(args.directory))


def clean(parser, subparser, args):
    assert nested_invoke not in os.environ
    commands.clean(commands.get_package_dir(args.directory))


def list_files(parser, subparser, args):
    assert nested_invoke not in os.environ
    files = commands.list_files(commands.get_package_dir(args.directory),
                                args.include_implicit, args.strict)

    if args.json:
        print(json.dumps(files))
    else:
        for i in files:
            print(i)


def main():
    parser = argparse.ArgumentParser(prog='mopack')
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + version)
    parser.add_argument('--verbose', action='store_true',
                        help='show verbose output')
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
    subparsers.required = True

    resolve_p = subparsers.add_parser(
        'resolve', help='fetch and build package dependencies'
    )
    resolve_p.set_defaults(func=resolve, parser=resolve_p)
    resolve_p.add_argument('--directory', default='.', type=os.path.abspath,
                           metavar='PATH',
                           help='directory to store local package data in')
    resolve_p.add_argument('-P', '--deploy-path', action=KeyValueAction,
                           dest='deploy_paths', metavar='TYPE=PATH',
                           help='directories to deploy packages to')
    resolve_p.add_argument('-o', '--option', action=ConfigOptionAction,
                           dest='options', metavar='OPTION=VALUE',
                           help='additional common options')
    resolve_p.add_argument('-S', '--source-option', action=ConfigOptionAction,
                           key=['sources'], dest='options',
                           metavar='OPTION=VALUE',
                           help='additional source options')
    resolve_p.add_argument('-B', '--builder-option', action=ConfigOptionAction,
                           key=['builders'], dest='options',
                           metavar='OPTION=VALUE',
                           help='additional builder options')
    resolve_p.add_argument('file', nargs='+',
                           help='the mopack configuration files')

    usage_p = subparsers.add_parser(
        'usage', help='retrieve usage info for a package'
    )
    usage_p.set_defaults(func=usage, parser=usage_p)
    usage_p.add_argument('-s', '--submodule', action='append',
                         dest='submodules',
                         help='the name of the submodule to use')
    usage_p.add_argument('--directory', default='.', type=os.path.abspath,
                         metavar='PATH',
                         help='directory storing local package data')
    usage_p.add_argument('--json', action='store_true',
                         help='display results as JSON')
    usage_p.add_argument('--strict', action='store_true',
                         help='return an error if package is not defined')
    usage_p.add_argument('package', help='the name of the package to query')

    deploy_p = subparsers.add_parser(
        'deploy', help='deploy packages'
    )
    deploy_p.set_defaults(func=deploy, parser=deploy_p)
    deploy_p.add_argument('--directory', default='.', type=os.path.abspath,
                          metavar='PATH',
                          help='directory storing local package data')

    clean_p = subparsers.add_parser(
        'clean', help='clean package directory'
    )
    clean_p.set_defaults(func=clean, parser=clean_p)
    clean_p.add_argument('--directory', default='.', type=os.path.abspath,
                         metavar='PATH',
                         help='directory storing local package data')

    list_files_p = subparsers.add_parser(
        'list-files', help='list input files'
    )
    list_files_p.set_defaults(func=list_files, parser=list_files_p)
    list_files_p.add_argument('--directory', default='.', type=os.path.abspath,
                              metavar='PATH',
                              help='directory storing local package data')
    list_files_p.add_argument('-I', '--include-implicit', action='store_true',
                              help='include implicit input files')
    list_files_p.add_argument('--json', action='store_true',
                              help='display results as JSON')
    list_files_p.add_argument('--strict', action='store_true',
                              help='return an error if package is not defined')

    args = parser.parse_args()
    log.init(args.color, debug=args.debug, verbose=args.verbose,
             warn_once=args.warn_once)

    try:
        return args.func(parser, args.parser, args)
    except Exception as e:
        logger.exception(e)
        return 1
