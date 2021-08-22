from . import *


class HelpTest(SubprocessTestCase):
    def test_help(self):
        output = self.assertPopen(['mopack', 'help'])
        self.assertRegex(output, r'^usage: mopack \[-h\] \[--version\]')

    def test_help_subcommand(self):
        output = self.assertPopen(['mopack', 'help', 'resolve'])
        self.assertRegex(output, r'^usage: mopack resolve \[-h\]')

    def test_help_subcommand_extra(self):
        output = self.assertPopen(['mopack', 'help', 'resolve', 'mopack.yml'])
        self.assertRegex(output, r'^usage: mopack resolve \[-h\]')
