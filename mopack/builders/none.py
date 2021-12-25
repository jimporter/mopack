from . import Builder


class NoneBuilder(Builder):
    type = 'none'
    _version = 1

    @staticmethod
    def upgrade(config, version):
        return config

    def path_bases(self):
        return ()

    def path_values(self, pkgdir):
        return {}

    def _builddir(self, pkgdir):
        raise NotImplementedError()

    def clean(self, pkgdir):
        pass

    def build(self, pkgdir, srcdir):
        pass

    def deploy(self, pkgdir, srcdir):
        pass
