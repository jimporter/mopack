from . import Builder


class NoneBuilder(Builder):
    type = 'none'
    _version = 2

    def __init__(self, name, *, _symbols, **kwargs):
        super().__init__(name, **kwargs)

    @staticmethod
    def upgrade(config, version):
        # v2 removes the name field.
        if version < 2:  # pragma: no branch
            del config['name']
        return config

    def path_bases(self):
        return ()

    def path_values(self, metadata):
        return {}

    def clean(self, metadata, pkg):
        pass

    def build(self, metadata, pkg):
        pass

    def deploy(self, metadata, pkg):
        pass
