from Cython.Build import cythonize

# use cythonize to build the extensions
modules = [
    # "runekit/image/format.pyx",
]

extensions = cythonize(modules)


def build(setup_kwargs):
    """Needed for the poetry building interface."""

    setup_kwargs.update({"ext_modules": extensions, "scripts": ["main.py"]})
