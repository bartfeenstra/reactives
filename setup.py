"""Integrates Reactives with Python's setuptools."""

from pathlib import Path

from setuptools import setup, find_packages

ROOT_DIRECTORY_PATH = Path(__file__).resolve().parent

with open(ROOT_DIRECTORY_PATH / 'VERSION') as f:
    VERSION = f.read()

with open(ROOT_DIRECTORY_PATH / 'README.md') as f:
    long_description = f.read()

SETUP = {
    'name': 'reactives',
    'description': 'A declarative reactive programming framework.',
    'long_description': long_description,
    'long_description_content_type': 'text/markdown',
    'version': VERSION,
    'license': 'GPLv3',
    'author': 'Bart Feenstra & contributors',
    'author_email': 'bart@mynameisbart.com',
    'url': 'https://github.com/bartfeenstra/reactives',
    'classifiers': [
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Typing :: Typed',
    ],
    'python_requires': '~= 3.8',
    'install_requires': [
        'graphlib-backport ~= 1.0, >= 1.0.3; python_version < "3.9"',
        'typing_extensions ~= 4.4, >= 4.4.0; python_version < "3.11"',
    ],
    'extras_require': {
        'development': [
            'autopep8 ~= 2.0, >= 2.0.2',
            'codecov ~= 2.1, >= 2.1.12',
            'coverage ~= 7.2, >= 7.2.4',
            'dill ~= 0.3, >= 0.3.4',
            'flake8 ~= 6.0, >= 6.0.0',
            'mypy ~= 1.2, >= 1.2.0',
            'parameterized ~= 0.9, >= 0.9.0',
            'pytest ~= 7.3, >= 7.3.1',
            'pytest-cov ~= 4.0, >= 4.0.0',
            'setuptools ~= 67.7, >= 67.7.2',
            'twine ~= 4.0, >= 4.0.2',
            'wheel ~= 0.40, >= 0.40.0',
        ],
    },
    'packages': find_packages(),
    'data_files': [
        ('', [
            'LICENSE.txt',
            'README.md',
            'VERSION',
        ])
    ],
    'package_data': {
        'reactives': [
            str(ROOT_DIRECTORY_PATH / 'reactives' / 'py.typed'),
            # Include the test API.
            str(ROOT_DIRECTORY_PATH / 'reactives' / 'tests' / '__init__.py'),
         ]
    },
}

if __name__ == '__main__':
    setup(**SETUP)
