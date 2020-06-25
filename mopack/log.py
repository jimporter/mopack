import colorama
import logging
import os
import shlex
import subprocess
import textwrap
import warnings
from logging import (getLogger, info, debug,  # noqa: F401
                     CRITICAL, ERROR, WARNING, INFO, DEBUG)


class ColoredStreamHandler(logging.StreamHandler):
    _format_codes = {
        DEBUG: '1;35',
        INFO: '1;34',
        WARNING: '1;33',
        ERROR: '1;31',
        CRITICAL: '1;41;37',
    }

    def __init__(self, *args, debug=False, **kwargs):  # noqa: F811
        self.debug = debug
        super().__init__(*args, **kwargs)

    def format(self, record):
        record.coloredlevel = '\033[{format}m{name}\033[0m'.format(
            format=self._format_codes.get(record.levelno, '1'),
            name=record.levelname.lower()
        )
        return super().format(record)

    def emit(self, record):
        if not self.debug and record.exc_info:
            record.exc_info = None
        return super().emit(record)


def _init_logging(logger, debug, stream=None):  # noqa: F811
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    handler = ColoredStreamHandler(stream, debug=debug)
    fmt = '%(coloredlevel)s: %(message)s'
    handler.setFormatter(logging.Formatter(fmt))
    logger.addHandler(handler)


def init(color='auto', debug=False, warn_once=False):  # noqa: F811
    if color == 'always':
        colorama.init(strip=False)
    elif color == 'never':
        colorama.init(strip=True, convert=False)
    else:  # color == 'auto'
        colorama.init()

    warnings.filterwarnings('default')
    if warn_once:
        warnings.filterwarnings('once')

    _init_logging(logging.root, debug)


def _showwarning(message, category, filename, lineno, file=None, line=None):
    logging.log(WARNING, message)


warnings.showwarning = _showwarning


class LogFile:
    def __init__(self, file):
        self.file = file

    @classmethod
    def open(cls, pkgdir, name, mode='w'):
        logname = os.path.join(pkgdir, '{}.log'.format(name))
        return cls(open(logname, mode))

    def close(self):
        self.file.close()

    def check_call(self, args, **kwargs):
        command = ' '.join(shlex.quote(i) for i in args)
        print('$ ' + command, file=self.file, flush=True)
        try:
            result = subprocess.run(
                args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True, check=True
            )
            print(result.stdout, file=self.file)
        except subprocess.CalledProcessError as e:
            print(e.stdout, file=self.file)
            msg = "Command '{}' returned non-zero exit status {}".format(
                command, e.returncode
            )
            if e.stdout:
                msg += ':\n' + textwrap.indent(e.stdout.rstrip(), '  ')
            raise subprocess.SubprocessError(msg)
        except Exception as e:
            print(str(e), file=self.file)
            raise type(e)("Command '{}' failed:\n{}".format(
                command, textwrap.indent(str(e), '  ')
            ))

    def __enter__(self):
        self.file.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self.file.__exit__(exc_type, exc_value, traceback)
