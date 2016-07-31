#!/usr/bin/env python

try:
    import pypandoc
except ImportError:
    print("Install pypandoc to generate the field long_description")
    pypandoc = None
  
from setuptools import setup

if pypandoc:
    long_description = "\n\n".join([
        pypandoc.convert('README.md', 'rst'),
        pypandoc.convert('CHANGELOG.md', 'rst'),
    ])
else:
    long_description = "[pypandoc missing]"
 
setup(
    name='shoogle',
    version='0.1.3',
    description="Google API from the command line",
    long_description=long_description,
    author="Arnau Sanchez",
    author_email='pyarnau@gmail.com',
    url='https://github.com/tokland/shoogle',
    packages=[
        'shoogle',
        "shoogle/auth",
        "shoogle/commands",
    ],
    package_dir={'shoogle': 'shoogle'},
    scripts=["bin/shoogle"],
    include_package_data=True,
    install_requires=[
        "google-api-python-client",
        "jsmin",
        "httplib2",
    ],
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
    tests_require=[],
)
