from . import Builder


class NoneBuilder(Builder):
    type = 'none'
    _version = 3

    @staticmethod
    def upgrade(config, version):
        # v2 removes the name field.
        if version < 2:  # pragma: no branch
            del config['name']

        # v3 adds the `env` field.
        if version < 3:  # pragma: no branch
            config['env'] = {}

        return config
