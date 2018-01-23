from setuptools import setup, find_packages

setup(
    name='mara-db',
    version='2.1.1',

    description='Configuration and monitoring of database connections',

    install_requires=[
        'SQLAlchemy>=1.1.5',
        'multimethod>=0.7.1'
    ],

    dependency_links=[],

    packages=find_packages(),

    author='Mara contributors',
    license='MIT',

    entry_points={}
)
