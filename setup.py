import os
import re
from distutils.util import convert_path

from setuptools import Extension, find_packages, setup
from setuptools.command.build_ext import build_ext as _build_ext

try:
    from Cython.Build import cythonize
except ImportError as err:
    cythonize = err

# --- Utils -----------------------------------------------------------------


def _detect_target_machine(platform):
    if platform == "win32":
        return "x86"
    return platform.rsplit("-", 1)[-1]


def _detect_target_cpu(platform):
    machine = _detect_target_machine(platform)
    if re.match("^mips", machine):
        return "mips"
    elif re.match("^(aarch64|arm64)$", machine):
        return "aarch64"
    elif re.match("^arm", machine):
        return "arm"
    elif re.match("(x86_64)|(x86)|(AMD64|amd64)|(^i.86$)", machine):
        return "x86"
    elif re.match("^(powerpc|ppc)", machine):
        return "ppc"
    return None


def _detect_target_system(platform):
    if platform.startswith("win"):
        return "windows"
    elif platform.startswith("macos"):
        return "macos"
    elif platform.startswith("linux"):
        return "linux_or_android"
    elif platform.startswith("freebsd"):
        return "freebsd"
    return None


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


class build_ext(_build_ext):
    def initialize_options(self) -> None:
        _build_ext.initialize_options(self)
        self.target_machine = None
        self.target_cpu = None
        self.target_system = None

    def run(self):
        if isinstance(cythonize, ImportError):
            raise RuntimeError("Failed to import Cython") from cythonize

        self.extensions = cythonize(self.extensions,
                                    compiler_directives={
                                        "linetrace": True,
                                        "language_level": 3
                                    })
        for ext in self.extensions:  # this fixes a bug with setuptools
            ext._needs_stub = False
        _build_ext.run(self)
        self.target_machine = _detect_target_machine(self.plat_name)
        self.target_cpu = _detect_target_cpu(self.plat_name)
        self.target_system = _detect_target_system(self.plat_name)


SRC_DIR = "src"
PACKAGES = [SRC_DIR]

install_requires = ["cython", "numpy"]
setup_requires = ["cython"]

EXTENSIONS = [
]

main_ns = {}
ver_path = convert_path('metaSNV/__init__.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)

setup(
    name="metaSNV",
    version=main_ns['__version__'],
    description=
    "Pipeline for identification of SNV within a microbiome sample.",
    long_description=read("README.md"),
    long_description_content_type='text/markdown',
    keywords="snv metagenomics polymorphism",
    author="alentyn Bezshapkin",
    author_email=
    "valentyn.bezshapkin@micro.biol.ethz.ch",
    url="https://github.com/metasnv-tool/metaSNV",
    download_url="https://github.com/metasnv-tool/metaSNV",
    include_package_data=True,
    ext_modules=EXTENSIONS,
    install_requires=install_requires,
    cmdclass={'build_ext': build_ext},
    license="GNU GPLv3",
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
    ],
)