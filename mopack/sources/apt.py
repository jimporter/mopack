from . import BinaryPackage
from .. import log, types
from ..iterutils import uniques
from ..shell import get_cmd


class AptPackage(BinaryPackage):
    source = 'apt'

    def __init__(self, name, remote=None, repository=None, usage='system',
                 **kwargs):
        super().__init__(name, usage=usage, **kwargs)

        T = types.TypeCheck(locals(), self._expr_symbols)
        T.remote(types.maybe(types.string, default='lib{}-dev'.format(name)))
        T.repository(types.maybe(types.string))

    @classmethod
    def resolve_all(cls, pkgdir, packages):
        for i in packages:
            log.pkg_resolve(i.name, 'from {}'.format(cls.source))

        apt = get_cmd(packages[0]._common_options.env, 'APT', 'sudo apt-get')
        aptrepo = get_cmd(packages[0]._common_options.env,
                          'ADD_APT_REPOSITORY', 'sudo add-apt-repository')

        remotes = [i.remote for i in packages]
        repositories = uniques(i.repository for i in packages if i.repository)

        with log.LogFile.open(pkgdir, 'apt') as logfile:
            for i in repositories:
                logfile.check_call(aptrepo + ['-y', i])
            logfile.check_call(apt + ['update'])
            logfile.check_call(apt + ['install', '-y'] + remotes)

        for i in packages:
            i.resolved = True

    @staticmethod
    def deploy_all(pkgdir, packages):
        pass
