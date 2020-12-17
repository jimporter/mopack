from . import Builder


class NoneBuilder(Builder):
    type = 'none'
    _path_bases = ('srcdir',)

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
