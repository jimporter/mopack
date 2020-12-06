from . import Builder


class NoneBuilder(Builder):
    type = 'none'

    def __init__(self, name, *, submodules, **kwargs):
        super().__init__(name, **kwargs)

    def _builddir(self, pkgdir):
        return None

    def clean(self, pkgdir):
        pass

    def build(self, pkgdir, srcdir, deploy_paths={}):
        pass

    def deploy(self, pkgdir):
        pass
