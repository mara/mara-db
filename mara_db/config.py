"""Configuration of database connections"""

import sqlalchemy.engine.url

def database_urls() -> {str: sqlalchemy.engine.url}:
    """The list of database connections to use, by alias"""
    return {'mara': sqlalchemy.engine.url.make_url('postgresql+psycopg2://root@localhost/mara')}


def mara_db_alias() -> str:
    """The database alias for mara internal data"""
    return 'mara'


