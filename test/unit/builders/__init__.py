from mopack.usage import make_usage

from .. import OptionsTest


class BuilderTest(OptionsTest):
    def set_options(self, builder, common_options=None, this_options=None):
        options = self.make_options(common_options)
        if this_options:
            options['builders'][builder.type].accumulate(this_options)
        builder.set_options(options)

    def make_builder(self, *args, set_options=True, common_options=None,
                     this_options=None, usage=None, submodules=None,
                     symbols=None, **kwargs):
        if symbols is None:
            symbols = self.symbols

        if len(args) == 1:
            builder_type = self.builder_type
            name = args[0]
        else:
            builder_type, name = args

        if usage is not None:
            usage = make_usage(name, usage, submodules=submodules,
                               symbols=symbols)
        builder = builder_type(name, usage=usage, submodules=submodules,
                               symbols=symbols, **kwargs)

        if set_options:
            self.set_options(builder, common_options, this_options)
        return builder
