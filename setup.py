from setuptools import setup, find_packages

setup(
    name='mara-db',
    version='3.1.2',

    description='Configuration and monitoring of database connections',

    install_requires=[
        'SQLAlchemy>=1.1.5',
        'sqlalchemy-utils>=0.32.14',
        'alembic>=0.8.10',
        'multimethod>=0.7.1',
        'graphviz>=0.8',
        'mara-page>=1.3.0',
        'psycopg2-binary>=2.7.3'],

    dependency_links=[
        'git+https://github.com/mara/mara-page.git@1.3.0#egg=mara-page-1.3.0',
    ],

    packages=find_packages(),

    author='Mara contributors',
    license='MIT',

    entry_points={},
    python_requires='>=3.6'
)
