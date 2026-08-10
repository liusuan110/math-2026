"""Local version fallback for vendored tueplots source.

The upstream project generates this file from Git metadata via setuptools_scm.
This repository stores third-party sources without their .git directories, so
direct source imports need a small static fallback.
"""

version = "0+vendored"
__version__ = version
