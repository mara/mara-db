from setuptools import setup, find_packages

setup(
    name='mara-db',
    version='1.0.1',

    description='Configuration and monitoring of database connections',

    install_requires=[
        'SQLAlchemy>=1.1.5'
    ],

    dependency_links=[],

    packages=find_packages(),

    author='Mara contributors',
    license='MIT',

    entry_points={}
)
