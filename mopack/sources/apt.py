import subprocess
from itertools import chain

from . import BinaryPackage
from .. import log, types
from ..environment import get_cmd
from ..iterutils import uniques


class AptPackage(BinaryPackage):
    source = 'apt'
    _version = 1

    @staticmethod
    def upgrade(config, version):
        return config

    def __init__(self, name, *, remote=None, repository=None, usage='system',
                 **kwargs):
        super().__init__(name, usage=usage, **kwargs)

        T = types.TypeCheck(locals(), self._expr_symbols)
        T.remote(types.maybe(
            types.list_of(types.string, listify=True, allow_empty=False),
            default=['lib{}-dev'.format(name)]
        ))
        T.repository(types.maybe(types.string))

    def version(self, pkgdir):
        # XXX: Maybe try to de-munge the version into something not
        # apt-specific?
        dpkgq = get_cmd(self._common_options.env, 'DPKG_QUERY', 'dpkg-query')
        return subprocess.run(
            dpkgq + ['-W', '-f${Version}', self.remote[0]],
            check=True, stdout=subprocess.PIPE, universal_newlines=True
        ).stdout

    @classmethod
    def resolve_all(cls, packages, pkgdir):
        for i in packages:
            log.pkg_resolve(i.name, 'from {}'.format(cls.source))

        env = packages[0]._common_options.env
        apt = get_cmd(env, 'APT_GET', 'sudo apt-get')
        aptrepo = get_cmd(env, 'ADD_APT_REPOSITORY', 'sudo add-apt-repository')

        remotes = list(chain.from_iterable(i.remote for i in packages))
        repositories = uniques(i.repository for i in packages if i.repository)

        with log.LogFile.open(pkgdir, 'apt') as logfile:
            for i in repositories:
                logfile.check_call(aptrepo + ['-y', i])
            logfile.check_call(apt + ['update'])
            logfile.check_call(apt + ['install', '-y'] + remotes)

        for i in packages:
            i.resolved = True

    @staticmethod
    def deploy_all(packages, pkgdir):
        pass
