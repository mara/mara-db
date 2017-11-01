"""DB schema visualization"""

import binascii
import hashlib
from typing import List, Optional, Tuple
import functools

import flask
import graphviz
from sqlalchemy import engine

from mara_db import config, generic_db_helper
from mara_page import acl, navigation, response, bootstrap, _

TableDescriptor = Tuple[Optional[str], str, List[str]]

mara_db = flask.Blueprint('mara_db', __name__, static_folder='static', template_folder='templates', url_prefix='/db')

acl_resource = acl.AclResource(name='DB')

schema_colors = ['#8B0000', '#A52A2A', '#B22222', '#DC143C', '#FF0000', '#FF6347', '#FF7F50', '#CD5C5C', '#F08080',
                 '#E9967A', '#FA8072', '#FFA07A', '#FF4500', '#FF8C00', '#FFA500', '#FFD700', '#B8860B', '#DAA520',
                 '#EEE8AA', '#BDB76B', '#F0E68C', '#808000', '#FFFF00', '#9ACD32', '#556B2F', '#6B8E23', '#7CFC00',
                 '#7FFF00', '#ADFF2F', '#006400', '#008000', '#228B22', '#00FF00', '#32CD32', '#90EE90', '#98FB98',
                 '#8FBC8F', '#00FA9A', '#00FF7F', '#2E8B57', '#66CDAA', '#3CB371', '#20B2AA', '#2F4F4F', '#008080',
                 '#008B8B', '#00FFFF', '#00FFFF', '#E0FFFF', '#00CED1', '#40E0D0', '#48D1CC', '#AFEEEE', '#7FFFD4',
                 '#B0E0E6', '#5F9EA0', '#4682B4', '#6495ED', '#00BFFF', '#1E90FF', '#ADD8E6', '#87CEEB', '#87CEFA',
                 '#191970', '#000080', '#00008B', '#0000CD', '#0000FF', '#4169E1', '#8A2BE2', '#4B0082', '#483D8B',
                 '#6A5ACD', '#7B68EE', '#9370DB', '#8B008B', '#9400D3', '#9932CC', '#BA55D3', '#800080', '#D8BFD8',
                 '#DDA0DD', '#EE82EE', '#FF00FF', '#DA70D6', '#C71585', '#DB7093', '#FF1493', '#FF69B4', '#FFB6C1',
                 '#FFC0CB', '#FAEBD7', '#F5F5DC', '#FFE4C4', '#FFEBCD', '#F5DEB3', '#FFF8DC', '#FFFACD', '#FAFAD2',
                 '#FFFFE0', '#8B4513', '#A0522D', '#D2691E', '#CD853F', '#F4A460', '#DEB887', '#D2B48C', '#BC8F8F',
                 '#FFE4B5', '#FFDEAD']


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
        -> Tuple[str, List[TableDescriptor], List[generic_db_helper.FKRelationship]]:
    """
    Produce the representation and if requested the corrsponding SVG of the tables and FK relationships between tables of a set of schemas.
    Also include metadata about generated SVG (list of displayed tables, schemas and relationships)
    Args:
        db: database on which to operate
        schemas: list of schemas to consider
        hide_columns: if True, the chart will not show the column names
        generate_svg: whether or not generate the SVG
    Returns:
        A tuple with three elements in this order: the SVG as a string (or None if generate_svg is False)
        , the list of tables in it and the list of relationships
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
@acl.require_permission(acl_resource)
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


@mara_db.route('/json/<string:db_alias>/<string:schemas>')
@acl.require_permission(acl_resource)
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
@acl.require_permission(acl_resource)
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
