"""DB schema visualization"""

import binascii
import hashlib
from typing import Dict, List, Optional, Tuple
import functools

import flask
import graphviz
from sqlalchemy import engine

from mara_db import config, generic_db_helper
from mara_page import acl, navigation, response, bootstrap, _


mara_db = flask.Blueprint('mara_db', __name__, static_folder='static', template_folder='templates', url_prefix='/db')

acl_db_schema_access = acl.AclResource(name='DB')

schema_colors = ['#a6cee3',
                 '#1f78b4',
                 '#b2df8a',
                 '#33a02c',
                 '#fb9a99',
                 '#e31a1c',
                 '#fdbf6f',
                 '#ff7f00',
                 '#cab2d6',
                 '#6a3d9a',
                 '#ffff99',
                 '#b15928']


@functools.lru_cache(None)
def schema_color(name: str):
    """Give a string a color, always the same for the same string.
    Args:
       name: A string

    Returns:
       str: An RGB color in hex format, always the same for the same string
    """
    # no schema? Light gray
    if name is None:
        return '#EEEEEE'
    # python hash function is not guaranteed to give the same result across versions or implementations
    m = hashlib.sha256()
    m.update(name.encode())
    hash_index = int(binascii.hexlify(m.digest()), 16)
    return schema_colors[hash_index % len(schema_colors)]


def navigation_entry():
    return navigation.NavigationEntry(
        label='DB Schema', uri_fn=lambda: flask.url_for('mara_db.index_page', db_alias=config.mara_db_alias()),
        icon='star',
        description='Data base schemas',
        children=[navigation.NavigationEntry(label=db, icon='database',
                                             description=f'The schema of the {db} db',
                                             uri_fn=lambda current_db=db: flask.url_for('mara_db.index_page',
                                                                                        db_alias=current_db))
                  for db in config.databases().keys()]
    )


def draw_schema(db: engine.Engine, schemas: List[str] = [], hide_columns: bool = False, generate_svg: bool = True)\
        -> Tuple[Optional[str], Dict[str, List[str]], List[Tuple[str, str]]]:
    """
    Produce the representation and if requested the corrsponding SVG of the tables and FK relationships between tables of a set of schemas.
    Also include metadata about generated SVG (list of displayed tables, schemas and relationships)
    Args:
        db: database on which to operate
        schemas: list of schemas to consider
        hide_columns: if True, the chart will not show the column names
        generate_svg: whether or not generate the SVG
    Returns:
        A tuple with three elements in this order:
        * the SVG as a string (or None if generate_svg is False)
        * the list of tables in it
        * the list of foreign key relationships
    """
    # original: fdp, nicest:neato or twopi
    # 'dot', 'neato', 'twopi', 'circo', 'fdp', 'sfdp', 'patchwork', 'osage',
    if generate_svg:
        graph = graphviz.Digraph(engine='neato', graph_attr={'splines': 'True',
                                                             'overlap': 'ortho'})
        # graph = graphviz.Graph(engine='dot', graph_attr={'splines' : True, 'overlap' : 'ortho'})

        node_attributes = {'fontname': 'Helvetica, Arial, sans-serif',  # use website default
                           'fontsize': '9.0px'  # fontsize unfortunately must be set
                           }

    tables = generic_db_helper.list_tables_and_columns(db, schemas)
    fk_relationships = generic_db_helper.list_fk_constraints(db)

    for schema_name, table_name, columns in tables:
        # NOTE: there are limits on what can be put on a label.
        # To be considered HTML it has to start with < and end with >, no whitespaces before or after
        # only a few tags can be used, like FONT or TABLE
        # There are also limitations on what can be put inside a tag:
        # no text will cause a command line parse error, a whitespace however is fine
        # Many other rules apply, is convenient to check whether it works immediately
        # after each change as the error messages are not explicit
        # The tool is able to calculate the display size of the label and display edges in the correct position,
        # so there are no particular limits on the content of a node
        # However, columns names sometime overflow so a separator is added as a suffix and prefix to take some space
        separator = '      '
        if generate_svg:
            graph.node(shape='plain', name=f'{schema_name}___{table_name}',
                       label=''.join(['<',
                                      f""" <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="1" BGCOLOR="{schema_color(schema_name)}"><TR><TD ALIGN="LEFT"><U><B>""",
                                      f'{schema_name}.{table_name}' if len(schemas) > 1 else table_name,
                                      """</B></U></TD></TR>""", ''.join(
                               [f'<TR><TD ALIGN="LEFT" >{separator}{c}{separator}</TD></TR>' for c in
                                columns]) if not hide_columns else '',
                                      """"</TABLE> """,

                                      '>']), _attributes=node_attributes)
    shown_tables = {f'{s}___{t}': cols for (s, t, cols) in tables}
    shown_relationships: List[Tuple[str, str]] = []

    for rel in fk_relationships:
        source_name = f'{rel.source_schema}___{rel.source_table}'
        target_name = f'{rel.target_schema}___{rel.target_table}'
        if source_name in shown_tables and target_name in shown_tables:
            if generate_svg:
                graph.edge(source_name, target_name)
            shown_relationships.append((source_name, target_name))
    if generate_svg:
        return (graph.pipe('svg').decode('utf-8'), shown_tables, shown_relationships)
    else:
        return (None, shown_tables, shown_relationships)


@mara_db.route('/svg/<string:db_alias>/<string:schemas>')
@acl.require_permission(acl_db_schema_access)
def get_svg(db_alias: str, schemas: str):
    """Shows a chart of the tables and FK relationships in a given database and schema list"""
    if db_alias not in config.databases():
        return response.Response(status=400, title=f'unkown database {db_alias}',
                                 html=f'Error, database {db_alias} is unknown')

    db = config.databases()[db_alias]
    rendered_svg = draw_schema(db, schemas.split('|'), 'no_columns' in flask.request.args)
    return flask.jsonify({
        'svg': rendered_svg[0],
        'tables': rendered_svg[1],
        'relationships': rendered_svg[2]
    })


@mara_db.route('/json/<string:db_alias>/<string:schemas>.json')
@acl.require_permission(acl_db_schema_access)
def get_structure(db_alias: str, schemas: str):
    """Retrieve a JSON with the tables and FK relationships in a given database and schema list"""
    if db_alias not in config.databases():
        return response.Response(status=400, title=f'unkown database {db_alias}',
                                 html=f'Error, database {db_alias} is unknown')

    db = config.databases()[db_alias]
    description = draw_schema(db, schemas.split('|'), 'no_columns' in flask.request.args, generate_svg=False)
    return flask.jsonify({
        'tables': description[1],
        'relationships': description[2]
    })


@mara_db.route('/<string:db_alias>')
@acl.require_permission(acl_db_schema_access)
def index_page(db_alias: str):
    """Shows a page to let the user pick some schemas and see the tables and FK"""
    if db_alias not in config.databases():
        return response.Response(status=404, title=f'unkown database {db_alias}',
                                 html=[bootstrap.card(body=_.p(style='color:red')[
                                     'The database alias ',
                                     _.strong()[db_alias],
                                     ' is unknown'
                                 ])])

    db = config.databases()[db_alias]
    from mara_db import generic_db_helper
    available_schemas = generic_db_helper.list_schemas(db)
    if len(available_schemas) == 0:
        return response.Response(title=f'No schemas to display for {db_alias}',
                                 html=[bootstrap.card(
                                     body=f'The database source {db_alias} has no schemas suitable for displaying (no tables with foreign key constraints)')])

    schema_display = [{'name': s, 'color': schema_color(s)} for s in available_schemas]

    return response.Response(title=f'Schemas of {db_alias}',
                             html=flask.render_template('schema_display.html', schema_display=schema_display,
                                                        db_alias=db_alias),
                             action_buttons=[response.ActionButton('javascript:exportSVGFile()',
                                                                   'Export as SVG',
                                                                   'Save current chart as SVG',
                                                                   'save'), ])
