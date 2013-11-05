#! ../env/bin/python
import os
import sys
import patmat

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

setup(
    name='patmat',
    version=patmat.__version__,
    description='Functional-style recursive pattern matching in Python. '
                'Crazy stuff.',
    long_description=open('README.rst').read(),
    license=open('LICENSE').read(),
    author='Xitong Gao',
    author_email='@'.join(['gxtfmx', 'gmail.com']),
    url='https://github.com/admk/patmat',
    install_requires=[''],
    packages=['patmat'],
    include_package_data=True,
    scripts=[''],
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
    ),
    keywords='python, funtional programming, pattern matching',
    tests_require=['nose'],
    test_suite='tests',
)
