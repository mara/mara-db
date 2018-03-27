from setuptools import setup, find_packages

setup(
    name='mara-db',
    version='2.2.2',

    description='Configuration and monitoring of database connections',

    install_requires=[
        'SQLAlchemy>=1.1.5',
        'multimethod>=0.7.1',
        'graphviz>=0.8',
        'mara-page>=1.2.3'],

    dependency_links=[
        'git+ssh://git@github.com/mara/mara-page.git@1.2.3#egg=mara-page-1.2.3',
    ],

    packages=find_packages(),

    author='Mara contributors',
    license='MIT',

    entry_points={},
    python_requires='>=3.6'
)
