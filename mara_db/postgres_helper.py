from itertools import groupby
from typing import List, Tuple
from sqlalchemy import engine

from mara_db.views import FKRelationship

def list_schemas(db: engine.Engine) -> List[str]:
    """List the schema names in the given database.

    Args:
       db (:obj:`engine.Engine`): SQLAlchemy engine instance.

    Returns:
       List[str]: List of schema names
    """
    return [row['schema_name'] for row in db.execute("""select schema_name from information_schema.schemata""").fetchall()]


def list_tables_and_columns(db: engine.Engine, schema: str) -> List[Tuple[str, str, List[str]]]:
    """List the table names  in the given schema, ignoring inherited tables (only show father.

    Args:
       db (:obj:`engine.Engine`): SQLAlchemy engine instance.
       schema (:obj:`str`): The schema to search into.

    Returns:
       List[str, List[str]]: List of table names, without schema prefix, and their columns
    """
    raw_result = [(row['tablename'], row['column_name']) for row in db.execute("""select tablename, column_name
    from pg_tables pt
      JOIN information_schema.columns col
      ON col.table_name = pt.tablename AND col.table_schema = pt.schemaname
    where schemaname=%(schema_name)s AND tablename NOT IN (SELECT c.relname AS tablename
    FROM pg_inherits JOIN pg_class AS c ON (inhrelid=c.oid)
    JOIN pg_class as p ON (inhparent=p.oid))""", schema_name=schema).fetchall()]
    columns_dict = {}
    for table, column in raw_result:
        if table not in columns_dict:
            columns_dict[table] = []
        columns_dict[table].append(column)
    return [(schema, table, columns) for (table, columns) in columns_dict.items()]

def list_fk_constraints(db: engine.Engine) -> FKRelationship:
    """List the foreign key relationships in the whole databases.
        Includes cross-schema relationships

    Args:
       db (:obj:`engine.Engine`): SQLAlchemy engine instance.

    Returns:
       List[FKRelationship]: List of tuples with source and target table names and schemas
    """
    return [FKRelationship(row['constraint_schema_name'], row['constraint_table_name'], row['foreign_schema_name'], row['foreign_table_name'])
            for row in db.execute('''
        WITH inheritance_relations AS
        (SELECT
        child_namespace.nspname  AS child_schema_name,
        child_class.relname      AS child_table_name,
        parent_namespace.nspname AS parent_schema_name,
        parent_class.relname     AS parent_table_name
        FROM pg_inherits
        JOIN pg_class parent_class ON parent_class.OID = pg_inherits.inhparent
        JOIN pg_class child_class ON child_class.OID = pg_inherits.inhrelid
        JOIN pg_namespace parent_namespace ON parent_class.relnamespace = parent_namespace.OID
        JOIN pg_namespace child_namespace ON child_class.relnamespace = child_namespace.OID) 
        SELECT
        DISTINCT
        coalesce(constraint_inheritance.parent_schema_name, constraint_schema.nspname) AS constraint_schema_name,
        coalesce(constraint_inheritance.parent_table_name, constraint_table.relname)   AS constraint_table_name,
        source_column.attname                                                          AS constraint_column_name,
        coalesce(foreign_inheritance.parent_schema_name, foreign_schema.nspname)       AS foreign_schema_name,
        coalesce(foreign_inheritance.parent_table_name, foreign_table.relname)         AS foreign_table_name
        FROM pg_constraint
        JOIN pg_class constraint_table ON constraint_table.oid = pg_constraint.conrelid
        JOIN pg_namespace constraint_schema ON constraint_schema.oid = constraint_table.relnamespace
        JOIN pg_class foreign_table ON foreign_table.oid = pg_constraint.confrelid
        JOIN pg_namespace foreign_schema ON foreign_schema.oid = foreign_table.relnamespace
        JOIN pg_attribute source_column
        ON source_column.attnum = ANY (pg_constraint.conkey) AND source_column.attrelid = constraint_table.oid
        
        LEFT JOIN inheritance_relations constraint_inheritance
        ON constraint_inheritance.child_schema_name = constraint_schema.nspname AND
        constraint_inheritance.child_table_name = constraint_table.relname
        
        LEFT JOIN inheritance_relations foreign_inheritance
        ON foreign_inheritance.child_schema_name = foreign_schema.nspname AND
        foreign_inheritance.child_table_name = foreign_table.relname
        WHERE contype = 'f'
                                                   ''').fetchall()]
