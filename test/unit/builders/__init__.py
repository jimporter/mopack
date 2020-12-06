from mopack.usage import make_usage

from .. import OptionsTest


class BuilderTest(OptionsTest):
    def make_options(self, builder_type=None, *, common_options=None,
                     this_options=None):
        options = super().make_options(common_options)
        if this_options:
            type = (builder_type or self.builder_type).type
            options.builders[type].accumulate(this_options)
        return options

    def make_builder(self, *args, common_options=None, this_options=None,
                     usage=None, submodules=None, **kwargs):
        if len(args) == 1:
            builder_type = self.builder_type
            name = args[0]
        else:
            builder_type, name = args

        opts = self.make_options(builder_type, common_options=common_options,
                                 this_options=this_options)
        if usage is not None:
            usage = make_usage(name, usage, submodules=submodules,
                               _options=opts)
        return builder_type(name, usage=usage, submodules=submodules,
                            _options=opts, **kwargs)
