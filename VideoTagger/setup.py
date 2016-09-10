#!/usr/bin/env python3
from setuptools import setup, find_packages

###################################################################

CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: End Users/Desktop",
    "Natural Language :: English",
    "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
    "Operating System :: Unix",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
    "Topic :: Utilities",
]

INSTALL_REQUIRES = ['python_mpv_zws', 'PyYAML']  # note: gi a dependency from OS package - e.g. python-gobject

###################################################################
# # BOILER PLATE CODE


setup(
    name="VideoTagger",
    description="GTK 3.x research tool to take timestamped tags/notes of streamed or locally played video."
                "Uses MPV player.",
    license="GNU General Public License v3 or later (GPLv3+)",
    url="https://www.zaziork.com",
    version=open('VideoTagger/VERSION.rst').read(),
    author="Dan Bright",
    author_email="productions@zaziork.com",
    maintainer="Dan Bright",
    maintainer_email="productions@zaziork.com",
    keywords=["MPV", "video tagger", "video note taker", "video timestamper", "video research tool"],
    long_description=open('README.rst').read(),
    packages=find_packages() + ['VideoTagger/resources'],
    package_dir={"VideoTagger": "VideoTagger"},
    zip_safe=False,
    classifiers=CLASSIFIERS,
    install_requires=INSTALL_REQUIRES,
    include_package_data=True
)
