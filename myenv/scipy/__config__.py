# This file is generated by SciPy's build process
# It contains system_info results at the time of building this package.
from enum import Enum

__all__ = ["show"]
_built_with_meson = True


class DisplayModes(Enum):
    stdout = "stdout"
    dicts = "dicts"


def _cleanup(d):
    """
    Removes empty values in a `dict` recursively
    This ensures we remove values that Meson could not provide to CONFIG
    """
    if isinstance(d, dict):
        return { k: _cleanup(v) for k, v in d.items() if v != '' and _cleanup(v) != '' }
    else:
        return d


CONFIG = _cleanup(
    {
        "Compilers": {
            "c": {
                "name": "clang",
                "linker": "ld64",
                "version": "12.0.0",
                "commands": "cc",
            },
            "cython": {
                "name": "cython",
                "linker": "cython",
                "version": "0.29.33",
                "commands": "cython",
            },
            "c++": {
                "name": "clang",
                "linker": "ld64",
                "version": "12.0.0",
                "commands": "c++",
            },
            "fortran": {
                "name": "gcc",
                "linker": "ld64",
                "version": "4.9.0",
                "commands": "gfortran",
            },
            "pythran": {
                "version": "0.12.1",
                "include directory": r"/private/var/folders/24/8k48jl6d249_n_qfxwsl6xvm0000gn/T/pip-build-env-ynq8myou/overlay/lib/python3.8/site-packages/pythran"
            },
        },
        "Machine Information": {
            "host": {
                "cpu": "x86_64",
                "family": "x86_64",
                "endian": "little",
                "system": "darwin",
            },
            "build": {
                "cpu": "x86_64",
                "family": "x86_64",
                "endian": "little",
                "system": "darwin",
            },
            "cross-compiled": bool("False".lower().replace('false', '')),
        },
        "Build Dependencies": {
            "blas": {
                "name": "OpenBLAS",
                "found": bool("True".lower().replace('false', '')),
                "version": "0.3.18",
                "detection method": "cmake",
                "include directory": r"unknown",
                "lib directory": r"unknown",
                "openblas configuration": "unknown",
                "pc file directory": r"unknown",
            },
            "lapack": {
                "name": "OpenBLAS",
                "found": bool("True".lower().replace('false', '')),
                "version": "0.3.18",
                "detection method": "cmake",
                "include directory": r"unknown",
                "lib directory": r"unknown",
                "openblas configuration": "unknown",
                "pc file directory": r"unknown",
            },
        },
        "Python Information": {
            "path": r"/private/var/folders/24/8k48jl6d249_n_qfxwsl6xvm0000gn/T/cibw-run-uowbple5/cp38-macosx_x86_64/build/venv/bin/python",
            "version": "3.8",
        },
    }
)


def _check_pyyaml():
    import yaml

    return yaml


def show(mode=DisplayModes.stdout.value):
    """
    Show libraries and system information on which SciPy was built
    and is being used

    Parameters
    ----------
    mode : {`'stdout'`, `'dicts'`}, optional.
        Indicates how to display the config information.
        `'stdout'` prints to console, `'dicts'` returns a dictionary
        of the configuration.

    Returns
    -------
    out : {`dict`, `None`}
        If mode is `'dicts'`, a dict is returned, else None

    Notes
    -----
    1. The `'stdout'` mode will give more readable
       output if ``pyyaml`` is installed

    """
    if mode == DisplayModes.stdout.value:
        try:  # Non-standard library, check import
            yaml = _check_pyyaml()

            print(yaml.dump(CONFIG))
        except ModuleNotFoundError:
            import warnings
            import json

            warnings.warn("Install `pyyaml` for better output", stacklevel=1)
            print(json.dumps(CONFIG, indent=2))
    elif mode == DisplayModes.dicts.value:
        return CONFIG
    else:
        raise AttributeError(
            f"Invalid `mode`, use one of: {', '.join([e.value for e in DisplayModes])}"
        )
