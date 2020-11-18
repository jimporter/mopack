from . import Builder


class NoneBuilder(Builder):
    type = 'none'

    def __init__(self, name, *, usage, submodules=None, **kwargs):
        super().__init__(name, usage=usage, **kwargs)

    def clean(self, pkgdir):
        pass

    def build(self, pkgdir, srcdir, deploy_paths={}):
        pass

    def deploy(self, pkgdir):
        pass
