import glob
import pathlib
import os

from setuptools import find_packages
from setuptools import setup

MY_DIRECTORY = os.path.dirname(__file__)


def readme():
    """Returns the contents of the package README.md."""
    return (
        pathlib.Path(__file__)
        .parent
        .joinpath('README.md')
        .read_text()
    )


def populate_extra_files():
    """
    Creates a list of non-python files to include in package distribution
    """
    root = pathlib.Path(__file__).parent.joinpath('reviser').absolute()
    globs = [root.joinpath('**/*.jinja2')]
    return list({
        entry
        for pattern in globs
        for entry in glob.iglob(str(pattern), recursive=True)
    })


setup(
    name='reviser',
    description='AWS Lambda function/layer version deployment manager.',
    long_description=readme(),
    keywords=[
        'AWS', 'Lambda',
        'Interactive', 'Interpreter', 'Shell'
    ],
    url='https://github.com/sernst/reviser',
    author='Scott Ernst',
    author_email='swernst@gmail.com',
    license='MIT',
    platforms='Linux, Mac OS X, Windows',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    package_data={'': populate_extra_files()},
    include_package_data=True,
    zip_safe=False,
    entry_points=dict(
        console_scripts=['reviser=reviser.cli:main']
    ),
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.8',
    ],
    python_requires='>=3.8',
    install_requires=[],
    extras_require={
        'shell': [
            'colorama',
            'pyyaml',
            'prompt_toolkit',
            'pipper',
            'jinja2',
        ],
    },
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'pytest-cov']
)
