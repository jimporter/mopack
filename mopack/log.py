import os
import subprocess


def open_log(pkgdir, name):
    logname = os.path.join(pkgdir, '{}.log'.format(name))
    os.makedirs(pkgdir, exist_ok=True)
    return open(logname, 'w')


def check_call_log(args, log):
    subprocess.check_call(args, stdout=log, stderr=log)
