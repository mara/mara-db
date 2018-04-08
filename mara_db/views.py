"""DB schema visualization"""

import datetime
import re

import flask
import graphviz

import mara_db.postgresql
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
            if isinstance(db, mara_db.dbs.PostgreSQLDB)  # for now, only show postgres schemas
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


@blueprint.route('/<string:db_alias>/.schemas')
def schema_selection(db_alias: str):
    """Asynchronously computes the list of schemas with foreign key constraints"""
    schemas_with_fk_constraints = []
    with mara_db.postgresql.postgres_cursor_context(db_alias) as cursor:
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
            schemas_with_fk_constraints = sorted(list(set(result[0])))

    if len(schemas_with_fk_constraints) == 0:
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
        _.script['''
var schemaPage = SchemaPage("''' + flask.url_for('mara_db.index_page', db_alias=db_alias) + '''", "''' + db_alias + '''");
''']]))


@blueprint.route('/<string:db_alias>/<path:schemas>')
@acl.require_permission(acl_resource, do_abort=False)
def draw_schema(db_alias: str, schemas: str):
    """Shows a chart of the tables and FK relationships in a given database and schema list"""

    if db_alias not in config.databases():
        flask.abort(404, f'unkown database {db_alias}')

    db = dbs.db(db_alias)
    assert (isinstance(db, mara_db.dbs.PostgreSQLDB))  # currently only postgresql is supported

    schema_names = schemas.split('/')
    hide_columns = flask.request.args.get('hide-columns')

    # get all table inheritance relations as dictionary: {(child_schema, child_table): (parent_schema, parent_table)
    inherited_tables = {}
    with mara_db.postgresql.postgres_cursor_context(db_alias) as cursor:
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

    # get all tables that that have foreign key constrains on them or are referenced by foreign key constraints
    fk_constraints = set()  # {((table_schema, table_name), (referred_schema_name, referred_table_name)}
    constrained_columns = {}  # {(schema_name, table_name): {columns}}
    tables = set()

    with mara_db.postgresql.postgres_cursor_context(db_alias) as cursor:
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
        for schema_name, table_name, table_columns, referred_schema_name, referred_table_name in cursor.fetchall():
            referring_table = (schema_name, table_name)
            if referring_table in inherited_tables:
                referring_table = inherited_tables[referring_table]
            tables.add(referring_table)
            referred_table = (referred_schema_name, referred_table_name)
            if referred_table in inherited_tables:
                referred_table = inherited_tables[referred_table]
            tables.add(referred_table)
            fk_constraints.add((referring_table, referred_table))
            if referring_table in constrained_columns:
                constrained_columns[referring_table].update(table_columns)
            else:
                constrained_columns[referring_table] = set(table_columns)

    # get all columns of all tables
    table_columns = {}  # {(schema_name, table_name): [columns]}
    with mara_db.postgresql.postgres_cursor_context(db_alias) as cursor:
        cursor.execute('''
SELECT
  table_schema, table_name,
  array_agg(column_name :: TEXT ORDER BY ordinal_position)
FROM information_schema.columns
GROUP BY table_schema, table_name''')
        for schema_name, table_name, columns in cursor.fetchall():
            table_columns[(schema_name, table_name)] = columns

    graph = graphviz.Digraph(engine='neato' if hide_columns else 'fdp',
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
            for column in table_columns[(schema_name, table_name)]:
                label += '<TR><TD ALIGN="LEFT" > '
                if fk_pattern.match(column) \
                        and (schema_name, table_name) in constrained_columns \
                        and column not in constrained_columns[(schema_name, table_name)]:
                    label += '<B><I><FONT COLOR="#dd55dd"> ' + column + ' </FONT></I></B>'
                else:
                    label += column
                label += ' </TD></TR>'

        label += '</TABLE> >'

        graph.node(name=node_name, label=label,
                   _attributes={'fontname': 'Helvetica, Arial, sans-serif', 'fontsize': '10',
                                'fontcolor': '#555555', 'shape': 'none'})

    for (schema_name, table_name), (referred_schema_name, referred_table_name) in fk_constraints:
        graph.edge(schema_name + '.' + table_name, referred_schema_name + '.' + referred_table_name,
                   _attributes={'color': '#888888'})

    response = flask.Response(graph.pipe('svg').decode('utf-8'))
    response.headers[
        'Content-Disposition'] = f'attachment; filename="{datetime.date.today().isoformat()}-{db_alias}.svg"'
    return response
