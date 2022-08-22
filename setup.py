from setuptools import setup

setup(
    install_requires=[
        'SQLAlchemy>=1.1.5',
        'sqlalchemy-utils>=0.32.14',
        'alembic>=0.8.10',
        'multimethod>=1.0.0',
        'graphviz>=0.8',
        'mara-page>=1.3.0',
        'psycopg2-binary>=2.7.3'],

    extras_require={
        'test': ['pytest', 'pytest_click', 'pytest-docker', 'pytest-dependency', 'SQLAlchemy>=1.2.0'],

        # database requirements
        'bigquery':
            ['google-cloud-bigquery', # Google maintained bigquery client
             'google-cloud-bigquery-storage', # avoid warnigns in cursor contexts
             'pyarrow', # For pandas to bigquery
             'sqlalchemy-bigquery'
        ],
        'mssql': ['pyodbc'],
        'mysql': ['mysqlclient'],
        'postgres': ['psycopg2-binary>=2.7.3'],
        'redshift': ['psycopg2-binary>=2.7.3',
                     'sqlalchemy-redshift'],
        'snowflake': [
            'snowflake-sqlalchemy'
        ],
        'databricks': [
            'databricks-sql-cli',
            'databricks-sql-connector',
            'sqlalchemy-databricks',
        ]
    }
)
