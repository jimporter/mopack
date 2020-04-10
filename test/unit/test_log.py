import inspect
import logging
import warnings
from io import StringIO
from unittest import mock, TestCase

from mopack import log

# Make sure we're referring to the .py file, not the .pyc file.
this_file = __file__.rstrip('c')


def current_lineno():
    return inspect.stack()[1][2]


class TestLogger(TestCase):
    @staticmethod
    def _level(levelno):
        return '\033[{format}m{name}\033[0m'.format(
            format=log.ColoredStreamHandler._format_codes.get(levelno, '1'),
            name=logging.getLevelName(levelno).lower()
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
            lineno = current_lineno() + 1
            raise RuntimeError('runtime error')
        except RuntimeError as e:
            self.logger.exception(e)
        self.assertEqual(self.out.getvalue(), (
            '{level}: runtime error\n' +
            'Traceback (most recent call last):\n' +
            '  File "{file}", line {line}, in test_exception\n' +
            "    raise RuntimeError('runtime error')\n" +
            'RuntimeError: runtime error\n'
        ).format(level=self._level(log.ERROR), file=this_file, line=lineno))


class TestShowWarning(TestCase):
    def test_warn(self):
        class EqualWarning(UserWarning):
            def __eq__(self, rhs):
                return type(self) == type(rhs)

        with mock.patch('logging.log') as mlog:
            warnings.warn('message', EqualWarning)
            mlog.assert_called_once_with(
                log.WARNING, EqualWarning('message')
            )


class TestInit(TestCase):
    def test_colors(self):
        with mock.patch('logging.addLevelName'), \
             mock.patch('logging.root.addHandler'), \
             mock.patch('logging.root.setLevel'):  # noqa
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
             mock.patch('colorama.init'):  # noqa
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
             mock.patch('colorama.init'):  # noqa
            with mock.patch('logging.root.setLevel') as mlevel:
                log.init()
                mlevel.assert_called_once_with(log.INFO)

            with mock.patch('logging.root.setLevel') as mlevel:
                log.init(debug=True)
                mlevel.assert_called_once_with(log.DEBUG)
