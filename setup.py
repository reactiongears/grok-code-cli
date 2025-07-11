# setup.py
from setuptools import setup, find_packages

setup(
    name='grok-cli',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'openai>=1.0.0',
        'click>=8.0.0',
        'prompt_toolkit>=3.0.0',
    ],
    entry_points={
        'console_scripts': [
            'grok = grok.main:cli',
        ],
    },
)