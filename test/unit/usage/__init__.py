from .. import OptionsTest


class UsageTest(OptionsTest):
    def set_options(self, usage, common_options=None):
        options = self.make_options(common_options)
        usage.set_options(options)

    def make_usage(self, *args, set_options=True, common_options=None,
                   submodules=None, **kwargs):
        if len(args) == 1:
            usage_type = self.usage_type
            name = args[0]
        else:
            usage_type, name = args

        usage = usage_type(name, submodules=submodules, **kwargs)

        if set_options:
            self.set_options(usage, common_options)
        return usage
