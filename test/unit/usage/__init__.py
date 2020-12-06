from .. import OptionsTest


class UsageTest(OptionsTest):
    def make_usage(self, *args, common_options=None, submodules=None,
                   **kwargs):
        if len(args) == 1:
            usage_type = self.usage_type
            name = args[0]
        else:
            usage_type, name = args

        opts = self.make_options(common_options)
        return usage_type(name, submodules=submodules, _options=opts, **kwargs)
