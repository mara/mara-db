from typing import List, NamedTuple, Optional, Set, Tuple

import sqlalchemy as sa

FKRelationship = NamedTuple("FKRelationship",
                            [('source_schema', Optional[str]), ('source_table', str), ('target_schema', Optional[str]),
                             ('target_table', str)])

def list_schemas(db: sa.engine.Engine) -> List[str]:
    """List the __relevant__ schema names in the given database. Ignores scheme without FK relationships inside

    Args:
       db: SQLAlchemy engine instance.

    Returns:
       List[str]: List of schema names where at least a FK relationship exists
    """

    schemas: Set[str] = set()
    for schema_name in sa.inspect(db).get_schema_names():
        # TODO determine whether the schema has FK constraints or not
        schemas.add(schema_name)

    return list(schemas)


def __list_schemas_and_tables(inspector, schemas: List[str] = None) -> List[Tuple[str, str]]:
    schemas_and_tables: List[Tuple[str, str]] = []
    if not schemas:
        schemas_and_tables = [(None, table_name) for table_name in inspector.get_table_names()]
    else:
        for schema in schemas:
            schemas_and_tables.extend([(schema, table_name) for table_name in inspector.get_table_names(schema)])
    return schemas_and_tables


def list_tables_and_columns(db: sa.engine.Engine, schemas: List[str]) -> List[Tuple[str, str, List[str]]]:
    """List the table names  in the given schema, ignoring inherited tables (only show father.

    Args:
       db: SQLAlchemy engine instance.
       schema: The schema to search into.

    Returns:
       List[str, str, List[str]]: List of schema and table names (without schema prefix) and their columns
       :param schemas: list of schema names
    """
    # TODO is it possible with SQLAlchemy/SQLAlchemy utils to manage table inheritance without special cases like this ?
    if db.dialect.name == 'postgresql':
        raw_result = [(row['cur_schema'], row['tablename'], row['column_name'])
                      for row in db.execute("""select tablename, column_name, col.table_schema AS cur_schema
        from pg_tables pt
          JOIN information_schema.columns col
          ON col.table_name = pt.tablename AND col.table_schema = pt.schemaname
        where schemaname IN %(schema_list)s AND tablename NOT IN (SELECT c.relname AS tablename
        FROM pg_inherits JOIN pg_class AS c ON (inhrelid=c.oid)
        JOIN pg_class as p ON (inhparent=p.oid))""", schema_list=tuple(schemas)).fetchall()]
        columns_dict = {}
        for schema, table, column in raw_result:
            if (schema, table) not in columns_dict:
                columns_dict[(schema, table)] = []
            columns_dict[(schema, table)].append(column)
        return [(schema, table, columns) for ((schema, table), columns) in columns_dict.items()]

    inspector = sa.engine.reflection.Inspector.from_engine(db)
    schemas_and_tables = __list_schemas_and_tables(inspector)

    res: List[Tuple[str, str, List[str]]] = []
    for (schema, table) in schemas_and_tables:
        # schema could be None, that is expected from DBMS like MySQL and SQLAlchemy accepts it
        res.append((schema, table, [t['name'] for t in inspector.get_columns(table, schema=schema)]))

    return res


def list_fk_constraints(db: sa.engine.Engine) -> FKRelationship:
    """List the foreign key relationships in the whole databases.
        Includes cross-schema relationships

    Args:
       db (:obj:`engine.Engine`): SQLAlchemy engine instance.

    Returns:
       List[FKRelationship]: List of tuples with source and target table names and schemas
    """
    inspector = sa.engine.reflection.Inspector.from_engine(db)
    schemas = inspector.get_schema_names()
    schemas_and_tables = __list_schemas_and_tables(inspector, schemas)
    result: List[FKRelationship] = []

    for (schema, table_name) in schemas_and_tables:
        tuned_schema = schema
        # workaround for strange SQLite behavior, see https://groups.google.com/forum/#!topic/sqlalchemy/rG-8JtiHXZE
        if tuned_schema == 'main' and db.dialect.name == 'sqlite':
            tuned_schema = None
        for fk in inspector.get_foreign_keys(table_name, schema=tuned_schema):
            result.append(FKRelationship(tuned_schema, table_name, fk.get('referred_schema', None), fk['referred_table']))
    return result
