from . import Builder


class NoneBuilder(Builder):
    type = 'none'
    _version = 1
    _path_bases = ('srcdir',)

    @staticmethod
    def upgrade(config, version):
        return config

    def __init__(self, name, *, submodules, **kwargs):
        super().__init__(name, **kwargs)

    def _builddir(self, pkgdir):
        return None

    def clean(self, pkgdir):
        pass

    def build(self, pkgdir, srcdir):
        pass

    def deploy(self, pkgdir, srcdir):
        pass
