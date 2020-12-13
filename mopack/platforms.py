import platform
import subprocess

from .objutils import memoize


def framework(name):
    return {'type': 'framework', 'name': name}


_package_library_names = {
    'posix': {
        'gl': 'GL',
        'glu': 'GLU',
        'zlib': 'z',
    },
    'darwin': {
        'gl': framework('OpenGL'),
        'glu': framework('OpenGL'),
        'glut': framework('GLUT'),
    },
    'windows': {
        'gl': 'opengl32',
        'glu': 'glu32',
        'glut': 'glut32',
    },
}


@memoize
def platform_name():
    system = platform.system().lower()
    if system.startswith('cygwin'):
        return 'cygwin'
    elif system == 'windows':
        try:
            uname = subprocess.check_output(
                'uname', universal_newlines=True
            ).lower()
            if uname.startswith('cygwin'):
                return 'cygwin'
        except OSError:
            pass

    return system


def package_library_name(platform, package):
    try:
        mapping = _package_library_names[platform]
    except KeyError:
        mapping = _package_library_names['posix']
    return mapping.get(package, package)
