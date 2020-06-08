from .. import OptionsTest


class BuilderTest(OptionsTest):
    def set_options(self, builder, common_options=None, this_options=None):
        options = self.make_options(common_options)
        if this_options:
            options['builders'][builder.type].accumulate(this_options)
        builder.set_options(options)

    def make_builder(self, *args, set_options=True, common_options=None,
                     this_options=None, submodules=None, **kwargs):
        if len(args) == 1:
            builder_type = self.builder_type
            name = args[0]
        else:
            builder_type, name = args

        builder = builder_type(name, submodules=submodules, **kwargs)

        if set_options:
            self.set_options(builder, common_options, this_options)
        return builder
