from typing import List

from setuptools import setup, find_packages


def get_requirements(filename: str = 'requirements.txt') -> List[str]:
    with open(filename, 'r') as r:
        return [x.strip() for x in r.readlines()]


setup(
    name='ts_metric_exporter',
    version='0.1.0',
    author='Dave-supertone',
    author_email='oceanlab@supertone.ai',
    packages=['ts_metric_exporter'],
    install_requires=get_requirements(),
    python_requires='>=3.6'
)