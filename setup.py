from setuptools import setup, find_packages
import re

def get_long_description():
    with open('README.md') as f:
        return re.sub('!\[(.*?)\]\(docs/(.*?)\)', r'![\1](https://github.com/mara/mara-db/raw/master/docs/\2)', f.read())

setup(
    name='mara-db',
    version='4.4.2',

    description='Configuration and monitoring of database connections',

    long_description=get_long_description(),
    long_description_content_type='text/markdown',

    url = 'https://github.com/mara/mara-db',

    install_requires=[
        'SQLAlchemy>=1.1.5',
        'sqlalchemy-utils>=0.32.14',
        'alembic>=0.8.10',
        'multimethod>=1.0.0',
        'graphviz>=0.8',
        'mara-page>=1.3.0',
        'psycopg2-binary>=2.7.3'],

    extras_require={
        'test': ['pytest', 'pytest_click'],
    },

    packages=find_packages(),

    author='Mara contributors',
    license='MIT',

    entry_points={},
    python_requires='>=3.6'
)
