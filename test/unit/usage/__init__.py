from .. import OptionsTest


class UsageTest(OptionsTest):
    def set_options(self, usage, general_options=None):
        options = self.make_options()
        if general_options:
            options['general'](**general_options)
        usage.set_options(options)

    def make_usage(self, *args, set_options=True, general_options=None,
                   submodules=None, **kwargs):
        if len(args) == 1:
            usage_type = self.usage_type
            name = args[0]
        else:
            usage_type, name = args

        usage = usage_type(name, submodules=submodules, **kwargs)

        if set_options:
            self.set_options(usage, general_options)
        return usage
