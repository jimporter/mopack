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

    def clean(self, pkg, pkgdir):
        pass

    def build(self, pkg, pkgdir):
        pass

    def deploy(self, pkg, pkgdir):
        pass
