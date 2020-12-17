from .. import OptionsTest, through_json  # noqa: F401


class BuilderTest(OptionsTest):
    def make_options(self, builder_type=None, *, common_options=None,
                     this_options=None, deploy_paths=None):
        options = super().make_options(common_options, deploy_paths)
        if this_options:
            type = (builder_type or self.builder_type).type
            options.builders[type].accumulate(this_options)
        return options

    def make_builder(self, *args, common_options=None, this_options=None,
                     deploy_paths=None, submodules=None, usage=None, **kwargs):
        if len(args) == 1:
            builder_type = self.builder_type
            name = args[0]
        else:
            builder_type, name = args

        opts = self.make_options(builder_type, common_options=common_options,
                                 this_options=this_options,
                                 deploy_paths=deploy_paths)
        builder = builder_type(name, submodules=submodules, _options=opts,
                               **kwargs)
        builder.set_usage(usage, submodules=submodules)
        return builder
