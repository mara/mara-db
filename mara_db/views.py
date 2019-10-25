"""DB schema visualization"""

import datetime
import re
import typing
from functools import singledispatch

import flask
from mara_db import config, dbs
from mara_page import acl, navigation, response, bootstrap, html, _, xml

blueprint = flask.Blueprint('mara_db', __name__, static_folder='static', template_folder='templates', url_prefix='/db')

acl_resource = acl.AclResource(name='DB Schema')


def navigation_entry():
    return navigation.NavigationEntry(
        label='DB Schema', icon='star', description='Data base schemas',
        children=[
            navigation.NavigationEntry(
                label=alias, icon='database',
                description=f'The schema of the {alias} db',
                uri_fn=lambda current_db=alias: flask.url_for('mara_db.index_page', db_alias=current_db))
            for alias, db in config.databases().items()
            if (isinstance(db, dbs.PostgreSQLDB) and not isinstance(db, dbs.RedshiftDB))
               or isinstance(db, dbs.MysqlDB)  # for now, only show postgres and mysql schemas
        ])


@blueprint.route('/<string:db_alias>')
def index_page(db_alias: str):
    """A page that visiualizes the schemas of a database"""
    if db_alias not in config.databases():
        flask.abort(404, f'unkown database {db_alias}')

    return response.Response(
        title=f'Schema of database {db_alias}',
        html=[bootstrap.card(sections=[
            html.asynchronous_content(flask.url_for('mara_db.schema_selection', db_alias=db_alias)),
            [_.div(id='schema-container')]]),
            html.spinner_js_function()],
        js_files=[flask.url_for('mara_db.static', filename='schema-page.js')],
        action_buttons=[response.ActionButton(
            action='javascript:schemaPage.downloadSvg()', label='SVG',
            title='Save current chart as SVG file', icon='download')]
    )


@singledispatch
def schemas_with_foreign_key_constraints(db: object) -> [str]:
    """
    Returns all schemas that are effected by foreign key constraints

    Args:
        db: The database in which to run the query (either an alias or a `dbs.DB` object
    """
    raise NotImplementedError(
        f'Please implement schemas_with_foreign_key_constraints for type "{db.__class__.__name__}"')


@schemas_with_foreign_key_constraints.register(str)
def __(alias: str):
    return schemas_with_foreign_key_constraints(dbs.db(alias))


@schemas_with_foreign_key_constraints.register(dbs.PostgreSQLDB)
def __(db: dbs.PostgreSQLDB):
    import mara_db.postgresql
    with mara_db.postgresql.postgres_cursor_context(db) as cursor:
        cursor.execute('''
SELECT
  array_cat(array_agg(DISTINCT constrained_table_schema.nspname), array_agg(DISTINCT referenced_table_schema.nspname))
FROM pg_constraint
  JOIN pg_class constrained_table ON constrained_table.oid = pg_constraint.conrelid
  JOIN pg_namespace constrained_table_schema ON constrained_table.relnamespace = constrained_table_schema.oid
  JOIN pg_class referenced_table ON referenced_table.oid = pg_constraint.confrelid
  JOIN pg_namespace referenced_table_schema ON referenced_table.relnamespace = referenced_table_schema.oid''')
        result = cursor.fetchone()
        if result != (None,):
            return list(set(result[0]))


@schemas_with_foreign_key_constraints.register(dbs.MysqlDB)
def __(db: dbs.MysqlDB):
    import mara_db.mysql
    with mara_db.mysql.mysql_cursor_context(db) as cursor:
        cursor.execute("""
SELECT DISTINCT table_schema
FROM information_schema.table_constraints
WHERE CONSTRAINT_TYPE = 'FOREIGN KEY'
UNION
SELECT DISTINCT REFERENCED_TABLE_SCHEMA
FROM information_schema.key_column_usage
WHERE REFERENCED_TABLE_SCHEMA IS NOT NULL;
""")
        return [row[0] for row in cursor.fetchall()]


@blueprint.route('/<string:db_alias>/.schemas')
def schema_selection(db_alias: str):
    """Asynchronously computes the list of schemas with foreign key constraints"""
    schemas_with_fk_constraints = schemas_with_foreign_key_constraints(db_alias)

    if not schemas_with_fk_constraints or len(schemas_with_fk_constraints) == 0:
        return str(_.i['No schemas with foreign key constraints found'])

    return ''.join(xml.render([
        [_.div(class_='form-check form-check-inline')[
             _.label(class_='form-check-label')[
                 _.input(class_="form-check-input schema-checkbox", type="checkbox", value=schema_name)[
                     ''], ' ', schema_name]]
         for schema_name in sorted(schemas_with_fk_constraints)],
        ' &#160;&#160;',
        _.div(class_='form-check form-check-inline')[
            _.label(class_='form-check-label')[
                _.input(class_="form-check-input", id='hide-columns-checkbox', type="checkbox")[
                    ''], ' ', 'hide columns']],
        ' &#160;&#160;',
        _.div(class_='form-check form-check-inline')[
            _.label(class_='form-check-label')[
                'graphviz engine ',
                _.select(id='engine', style='border:none;background-color:white;')[
                    [_.option(value=engine)[engine] for engine in ['neato', 'dot', 'twopi', 'fdp']]
                ]]],
        _.script['''
var schemaPage = SchemaPage("''' + flask.url_for('mara_db.index_page', db_alias=db_alias) + '''", "''' + db_alias + '''");
''']]))


@singledispatch
def extract_schema(db: object, schema_names: [str]) -> (typing.Dict, typing.Set):
    """
    Extracts foreign key constraints and the involved tables from a db

    Args:
        db: The database in which to run the query (either an alias or a `dbs.DB` object
        schema_names: the schemas to visualize

    Returns:
        A dictionary of tables:
            {(table_schema, table_name): {'columns': [columns], 'constrained-columns': {constrained-columns}}

        All foreign key constrains as a set of tuples:
            {((table_schema, table_name), (referenced_schema_name, referenced_table_name))}
    """
    raise NotImplementedError(f'Please implement extract_schema for type "{db.__class__.__name__}"')


@extract_schema.register(str)
def __(alias: str, schema_names: [str]):
    return extract_schema(dbs.db(alias), schema_names)


@extract_schema.register(dbs.PostgreSQLDB)
def __(db: dbs.PostgreSQLDB, schema_names: [str]):
    import mara_db.postgresql

    # get all table inheritance relations as dictionary: {(child_schema, child_table): (parent_schema, parent_table)
    inherited_tables = {}
    with mara_db.postgresql.postgres_cursor_context(db) as cursor:
        cursor.execute("""
SELECT
  rel_namespace.nspname, rel.relname ,
  parent_namespace.nspname, parent.relname
FROM pg_inherits
  JOIN pg_class parent ON parent.oid = pg_inherits.inhparent
  JOIN pg_class rel ON rel.oid = pg_inherits.inhrelid
  JOIN pg_namespace parent_namespace ON parent_namespace.oid = parent.relnamespace
  JOIN pg_namespace rel_namespace ON rel_namespace.oid = rel.relnamespace""")
        for schema_name, table_name, parent_schema_name, parent_table_name in cursor.fetchall():
            inherited_tables[(schema_name, table_name)] = (parent_schema_name, parent_table_name)

    # get all tables that have foreign key constrains on them or are referenced by foreign key constraints
    tables = {}  # {(table_schema, table_name): {'columns': [columns], 'constrained-columns': {constrained-columns}}
    foreign_key_constraints = set()  # {((table_schema, table_name), (referenced_schema_name, referenced_table_name)}

    def empty_table():
        return {'columns': [], 'constrained-columns': set()}

    with mara_db.postgresql.postgres_cursor_context(db) as cursor:
        cursor.execute(f'''
SELECT
  constrained_table_schema.nspname,
  constrained_table.relname,
  array_agg(constrained_column.attname),
  referenced_table_schema.nspname,
  referenced_table.relname
FROM pg_constraint
  JOIN pg_class constrained_table ON constrained_table.oid = pg_constraint.conrelid
  JOIN pg_namespace constrained_table_schema ON constrained_table.relnamespace = constrained_table_schema.oid
  JOIN pg_class referenced_table ON referenced_table.oid = pg_constraint.confrelid
  JOIN pg_namespace referenced_table_schema ON referenced_table.relnamespace = referenced_table_schema.oid
  JOIN pg_attribute constrained_column ON constrained_column.attrelid = constrained_table.oid AND attnum = ANY (conkey)
WHERE constrained_table_schema.nspname = ANY ({'%s'})
GROUP BY constrained_table_schema.nspname, constrained_table.relname, referenced_table_schema.nspname, referenced_table.relname;
''', (schema_names,))
        for schema_name, table_name, table_columns, referenced_schema_name, referenced_table_name in cursor.fetchall():
            referring_table = (schema_name, table_name)
            if referring_table in inherited_tables:
                referring_table = inherited_tables[referring_table]
            if referring_table not in tables:
                tables[referring_table] = empty_table()
            tables[referring_table]['constrained-columns'].update(table_columns)

            referenced_table = (referenced_schema_name, referenced_table_name)
            if referenced_table in inherited_tables:
                referenced_table = inherited_tables[referenced_table]

            if referenced_table not in tables:
                tables[referenced_table] = empty_table()

            foreign_key_constraints.add((referring_table, referenced_table))

    # get enum usages
    with mara_db.postgresql.postgres_cursor_context(db) as cursor:
        cursor.execute(f'''
SELECT
  DISTINCT
  pg_namespace_table.nspname AS table_schema,
  pg_class_table.relname     AS table_name,

  pg_namespace_enum.nspname  AS enum_schema,
  pg_type.typname            AS enum_type
FROM pg_attribute
  JOIN pg_class pg_class_table ON pg_class_table.oid = attrelid
  JOIN pg_namespace pg_namespace_table ON pg_namespace_table.oid = pg_class_table.relnamespace
  JOIN pg_type ON atttypid = pg_type.OID
  JOIN pg_namespace pg_namespace_enum ON typnamespace = pg_namespace_enum.oid
  JOIN pg_enum ON pg_enum.enumtypid = pg_type.oid
WHERE pg_namespace_table.nspname = ANY ({'%s'})''', (schema_names,))
        for table_schema, table_name, enum_schema, enum_name in cursor.fetchall():
            if (table_schema, table_name) in tables:
                if not (enum_schema, enum_name) in tables:
                    tables[(enum_schema, enum_name)] = empty_table()

                foreign_key_constraints.add(((table_schema, table_name), (enum_schema, enum_name)))

    # get all columns of all tables
    with mara_db.postgresql.postgres_cursor_context(db) as cursor:
        cursor.execute('''
SELECT
  table_schema, table_name,
  array_agg(column_name :: TEXT ORDER BY ordinal_position)
FROM information_schema.columns
GROUP BY table_schema, table_name''')
        for schema_name, table_name, columns in cursor.fetchall():
            if (schema_name, table_name) in tables:
                tables[(schema_name, table_name)]['columns'] = columns

    return tables, foreign_key_constraints


@extract_schema.register(dbs.MysqlDB)
def __(db: dbs.MysqlDB, schema_names: [str]):
    import mara_db.mysql

    # get all tables that have foreign key constrains on them or are referenced by foreign key constraints
    tables = {}  # {(table_schema, table_name): {'columns': [columns], 'constrained-columns': {constrained-columns}}
    foreign_key_constraints = set()  # {((table_schema, table_name), (referenced_schema_name, referenced_table_name)}

    def empty_table():
        return {'columns': [], 'constrained-columns': set()}

    with mara_db.mysql.mysql_cursor_context(db) as cursor:
        cursor.execute(f'''
SELECT i.table_schema,
       i.table_name,
       k.column_name,
       k.referenced_table_schema,
       k.referenced_table_name
FROM information_schema.table_constraints i
         LEFT JOIN information_schema.KEY_COLUMN_USAGE k
                   ON i.constraint_name = k.constraint_name
WHERE i.constraint_type = 'FOREIGN KEY' 
      AND k.referenced_table_name IS NOT NULL
      AND i.table_schema IN {'%s'}; ''', (schema_names,))
        for table_schema, table_name, column_name, referenced_table_schema, referenced_table_name in cursor.fetchall():
            referring_table = (table_schema, table_name)
            referenced_table = (referenced_table_schema, referenced_table_name)
            if not referring_table in tables:
                tables[referring_table] = empty_table()
            tables[referring_table]['constrained-columns'].add(column_name)

            if not referenced_table in tables:
                tables[referenced_table] = empty_table()

            foreign_key_constraints.add((referring_table, referenced_table))

    with mara_db.mysql.mysql_cursor_context(db) as cursor:
        cursor.execute(f'''
SELECT table_schema, table_name, column_name
FROM information_schema.COLUMNS
WHERE table_schema IN {'%s'}
''', (schema_names,))
        for table_schema, table_name, column_name in cursor.fetchall():
            if (table_schema, table_name) in tables:
                tables[(table_schema, table_name)]['columns'].append(column_name)

    return tables, foreign_key_constraints


@blueprint.route('/<string:db_alias>/<path:schemas>')
@acl.require_permission(acl_resource, do_abort=False)
def draw_schema(db_alias: str, schemas: str):
    """Shows a chart of the tables and FK relationships in a given database and schema list"""

    if db_alias not in config.databases():
        flask.abort(404, f'unkown database {db_alias}')

    schema_names = schemas.split('/')
    hide_columns = flask.request.args.get('hide-columns')
    engine = flask.request.args.get('engine')

    tables, fk_constraints = extract_schema(db_alias, schema_names)

    import graphviz
    graph = graphviz.Digraph(engine=engine,
                             graph_attr={'splines': 'True', 'overlap': 'ortho'})

    schema_colors = {}
    fk_pattern = re.compile(config.schema_ui_foreign_key_column_regex())
    for schema_name, table_name in sorted(tables):
        if schema_name not in schema_colors:
            colors = ['#ffffcc', '#bbffcc', '#cceeff', '#eedd99', '#ddee99', '#99ddff', '#dddddd']
            schema_colors[schema_name] = colors[len(schema_colors) % len(colors)]

        label = '< <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="1" BGCOLOR="' \
                + schema_colors[schema_name] + '"><TR>'

        node_name = schema_name + '.' + table_name
        if hide_columns:
            label += '<TD ALIGN="LEFT"> ' + table_name.replace('_', '<BR/>') + ' </TD></TR>'
        else:
            label += '<TD ALIGN="LEFT"><U><B> ' + table_name + ' </B></U></TD></TR>'
            for column in tables[(schema_name, table_name)]['columns']:
                label += '<TR><TD ALIGN="LEFT" > '
                if fk_pattern.match(column) \
                        and column not in tables[(schema_name, table_name)]['constrained-columns']:
                    label += '<B><I><FONT COLOR="#dd55dd"> ' + column + ' </FONT></I></B>'
                else:
                    label += column
                label += ' </TD></TR>'

        label += '</TABLE> >'

        graph.node(name=node_name, label=label,
                   _attributes={'fontname': 'Helvetica, Arial, sans-serif', 'fontsize': '10',
                                'fontcolor': '#555555', 'shape': 'none'})

    for (schema_name, table_name), (referenced_schema_name, referenced_table_name) in fk_constraints:
        graph.edge(schema_name + '.' + table_name, referenced_schema_name + '.' + referenced_table_name,
                   _attributes={'color': '#888888'})

    response = flask.Response(graph.pipe('svg').decode('utf-8'))
    response.headers[
        'Content-Disposition'] = f'attachment; filename="{datetime.date.today().isoformat()}-{db_alias}.svg"'
    return response
