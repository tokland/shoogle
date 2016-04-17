#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

requirements = [
    "google-api-python-client",
    "jsmin",
    "httplib2",
]

test_requirements = []

setup(
    name='shoogle',
    version='0.1.0',
    description="Google API from the command line",
    author="Arnau Sanchez",
    author_email='pyarnau@gmail.com',
    url='https://github.com/tokland/shoogle',
    packages=[
        'shoogle',
        "shoogle/auth"
    ],
    package_dir={'shoogle': 'shoogle'},
    scripts=["bin/shoogle"],
    include_package_data=True,
    install_requires=requirements,
    license="ISCL",
    zip_safe=False,
    keywords='shoogle',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Topic :: Internet :: WWW/HTTP',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    #tests_require=test_requirements,
)
