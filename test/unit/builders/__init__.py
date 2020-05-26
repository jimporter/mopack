from .. import OptionsTest


class BuilderTest(OptionsTest):
    def set_options(self, builder, global_options=None):
        options = self.make_options()
        if global_options:
            options['builders'][builder.type].accumulate(global_options)
        builder.set_options(options)

    def make_builder(self, *args, set_options=True, global_options=None,
                     submodules=None, **kwargs):
        if len(args) == 1:
            builder_type = self.builder_type
            name = args[0]
        else:
            builder_type, name = args

        builder = builder_type(name, submodules=submodules, **kwargs)

        if set_options:
            self.set_options(builder, global_options)
        return builder
