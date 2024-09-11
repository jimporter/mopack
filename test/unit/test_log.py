import inspect
import logging
import re
import warnings
from io import StringIO
from subprocess import SubprocessError
from unittest import mock, TestCase

from mopack import log
from mopack.iterutils import listify

# Make sure we're referring to the .py file, not the .pyc file.
this_file = __file__.rstrip('c')


def current_lineno():
    return inspect.stack()[1][2]


class TestCliColor(TestCase):
    def test_clicolor(self):
        self.assertEqual(log._clicolor({'CLICOLOR': '0'}), 'never')
        self.assertEqual(log._clicolor({'CLICOLOR': '1'}), 'auto')
        self.assertEqual(log._clicolor({'CLICOLOR': '2'}), 'auto')

    def test_clicolor_force(self):
        self.assertEqual(log._clicolor({'CLICOLOR_FORCE': '0'}), None)
        self.assertEqual(log._clicolor({'CLICOLOR_FORCE': '1'}), 'always')

    def test_neither(self):
        self.assertEqual(log._clicolor({}), None)

    def test_both(self):
        c = log._clicolor
        self.assertEqual(c({'CLICOLOR': '0', 'CLICOLOR_FORCE': '0'}), 'never')
        self.assertEqual(c({'CLICOLOR': '0', 'CLICOLOR_FORCE': '1'}), 'always')
        self.assertEqual(c({'CLICOLOR': '1', 'CLICOLOR_FORCE': '0'}), 'auto')
        self.assertEqual(c({'CLICOLOR': '1', 'CLICOLOR_FORCE': '1'}), 'always')


class TestLogger(TestCase):
    @staticmethod
    def _level(levelno):
        handler = log.ColoredStreamHandler
        name = logging.getLevelName(levelno).lower()
        fmt, indent = handler._format_codes.get(levelno, ('1', False))
        return '{space}\033[{format}m{name}\033[0m'.format(
            space=' ' * (handler._width - len(name)) if indent else '',
            format=fmt, name=name
        )

    def setUp(self):
        self.out = StringIO()
        self.logger = logging.getLogger(__name__)
        self.logger.propagate = False
        log._init_logging(self.logger, False, self.out)

    def test_info(self):
        self.logger.info('message')
        self.assertEqual(self.out.getvalue(),
                         '{}: message\n'.format(self._level(log.INFO)))

    def test_exception(self):
        try:
            raise RuntimeError('runtime error')
        except RuntimeError as e:
            self.logger.exception(e)
        self.assertEqual(self.out.getvalue(), (
            '{level}: runtime error\n'
        ).format(level=self._level(log.ERROR)))

    def test_exception_debug(self):
        logger = logging.getLogger(__name__ + 'debug')
        logger.propagate = False
        log._init_logging(logger, True, self.out)

        try:
            lineno = current_lineno() + 1
            raise RuntimeError('runtime error')
        except RuntimeError as e:
            logger.exception(e)
        self.assertEqual(self.out.getvalue(), (
            '{level}: runtime error\n' +
            'Traceback (most recent call last):\n' +
            '  File "{file}", line {line}, in test_exception_debug\n' +
            "    raise RuntimeError('runtime error')\n" +
            'RuntimeError: runtime error\n'
        ).format(level=self._level(log.ERROR), file=this_file, line=lineno))


class TestShowWarning(TestCase):
    def test_warn(self):
        class EqualWarning(UserWarning):
            def __eq__(self, rhs):
                return type(self) is type(rhs)

        with mock.patch('logging.log') as mlog:
            warnings.warn('message', EqualWarning)
            mlog.assert_called_once_with(
                log.WARNING, EqualWarning('message')
            )


class TestInit(TestCase):
    def test_colors(self):
        with mock.patch('logging.addLevelName'), \
             mock.patch('logging.root.addHandler'), \
             mock.patch('logging.root.setLevel'):
            with mock.patch('colorama.init') as mcolorama:
                log.init()
                mcolorama.assert_called_once_with()

            with mock.patch('colorama.init') as mcolorama:
                log.init(color='always')
                mcolorama.assert_called_once_with(strip=False)

            with mock.patch('colorama.init') as mcolorama:
                log.init(color='never')
                mcolorama.assert_called_once_with(strip=True, convert=False)

    def test_warn_once(self):
        with mock.patch('logging.addLevelName'), \
             mock.patch('logging.root.addHandler'), \
             mock.patch('logging.root.setLevel'), \
             mock.patch('colorama.init'):
            with mock.patch('warnings.filterwarnings') as mwarning:
                log.init()
                mwarning.assert_called_once_with('default')

            with mock.patch('warnings.filterwarnings') as mwarning:
                log.init(warn_once=True)
                self.assertEqual(mwarning.mock_calls, [
                    mock.call('default'),
                    mock.call('once')
                ])

    def test_debug(self):
        with mock.patch('logging.addLevelName'), \
             mock.patch('logging.root.addHandler'), \
             mock.patch('colorama.init'):
            with mock.patch('logging.root.setLevel') as mlevel:
                log.init()
                mlevel.assert_called_once_with(log.INFO)

            with mock.patch('logging.root.setLevel') as mlevel:
                log.init(debug=True)
                mlevel.assert_called_once_with(log.DEBUG)


class TestLogFile(TestCase):
    @staticmethod
    def mock_popen(returncode, *, cycles=1, stdout=''):
        stdout = listify(stdout)
        readline = stdout[:-1] + [''] * (cycles + 1 - len(stdout))
        read = stdout[-1] or ''

        mpopen = mock.MagicMock()
        mpopen.configure_mock(**{
            'returncode': returncode,
            'poll.side_effect': [None] * cycles + [returncode],
            'stdout.readline.side_effect': readline,
            'stdout.read.return_value': read,
        })
        return mpopen

    def test_with(self):
        with mock.patch('builtins.open', mock.mock_open()) as mopen:
            with log.LogFile.open('pkgdir', 'package'):
                pass
            mopen().__exit__.assert_called_once_with(None, None, None)

    def test_close(self):
        with mock.patch('builtins.open', mock.mock_open()) as mopen:
            logfile = log.LogFile.open('pkgdir', 'package')
            logfile.close()
            mopen().close.assert_called_once_with()

    def test_check_call(self):
        proc = self.mock_popen(0, stdout=['stdout\n', 'end\n'])
        with mock.patch('builtins.open', mock.mock_open()) as mopen, \
             mock.patch('subprocess.Popen', return_value=proc):
            with log.LogFile.open('pkgdir', 'package') as logfile:
                logfile.check_call(['cmd', '--arg'], env=None)
                output = ''.join(i[-2][0] for i in mopen().write.mock_calls)
                self.assertEqual(output, '$ cmd --arg\nstdout\nend\n')

    def test_check_call_proc_error_no_output(self):
        msg = "Command 'cmd --arg' returned non-zero exit status 1"
        with mock.patch('builtins.open', mock.mock_open()) as mopen, \
             mock.patch('subprocess.Popen', return_value=self.mock_popen(1)):
            with log.LogFile.open('pkgdir', 'package') as logfile:
                with self.assertRaisesRegex(SubprocessError, re.escape(msg)):
                    logfile.check_call(['cmd', '--arg'], env=None)
                output = ''.join(i[-2][0] for i in mopen().write.mock_calls)
                self.assertEqual(output, '$ cmd --arg\n')

    def test_check_call_proc_error_output(self):
        proc = self.mock_popen(1, stdout=['stdout\n', 'end\n'])
        msg = "Command 'cmd --arg' returned non-zero exit status 1"
        with mock.patch('builtins.open', mock.mock_open()) as mopen, \
             mock.patch('subprocess.Popen', return_value=proc):
            with log.LogFile.open('pkgdir', 'package') as logfile:
                with self.assertRaisesRegex(SubprocessError, re.escape(msg)):
                    logfile.check_call(['cmd', '--arg'], env=None)
                output = ''.join(i[-2][0] for i in mopen().write.mock_calls)
                self.assertEqual(output, '$ cmd --arg\nstdout\nend\n')

    def test_check_call_os_error(self):
        msg = "Command 'cmd --arg' failed:\n  bad"
        with mock.patch('builtins.open', mock.mock_open()) as mopen, \
             mock.patch('subprocess.Popen', side_effect=OSError('bad')):
            with log.LogFile.open('pkgdir', 'package') as logfile:
                with self.assertRaisesRegex(OSError, re.escape(msg)):
                    logfile.check_call(['cmd', '--arg'], env=None)
                output = ''.join(i[-2][0] for i in mopen().write.mock_calls)
                self.assertEqual(output, '$ cmd --arg\nbad\n')

    def test_synthetic_command(self):
        with mock.patch('builtins.open', mock.mock_open()) as mopen:
            with log.LogFile.open('pkgdir', 'package') as logfile:
                with logfile.synthetic_command(['cmd', '--arg']):
                    pass
                output = ''.join(i[-2][0] for i in mopen().write.mock_calls)
                self.assertEqual(output, '$ cmd --arg\n\n')

    def test_synthetic_command_error(self):
        with mock.patch('builtins.open', mock.mock_open()) as mopen:
            with log.LogFile.open('pkgdir', 'package') as logfile, \
                 self.assertRaises(RuntimeError):
                with logfile.synthetic_command(['cmd', '--arg']):
                    raise RuntimeError('bad')
            output = ''.join(i[-2][0] for i in mopen().write.mock_calls)
            self.assertEqual(output, '$ cmd --arg\nbad\n')
