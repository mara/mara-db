"""DB schema visualization"""

import binascii
import hashlib
from typing import List, NamedTuple, Optional, Tuple
import functools

import flask
import graphviz
from sqlalchemy import engine

from mara_db import config
from mara_page import acl, navigation, response, bootstrap, _

FKRelationship = NamedTuple("FKRelationship",
                            [('source_schema', Optional[str]), ('source_table', str), ('target_schema', Optional[str]),
                             ('target_table', str)])

mara_db = flask.Blueprint('mara_db', __name__, static_folder='static', url_prefix='/db')

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


def draw_schema(db: engine.Engine, schemas: List[str] = []) -> str:
    """
    Produce the SVG representation of the tables and FK relationships between tables of a set of schemas.
    """
    graph = graphviz.Graph(engine='fdp', graph_attr={'splines': 'True',
                                                     'overlap': 'ortho'})
    # graph = graphviz.Graph(engine='dot', graph_attr={'splines' : True, 'overlap' : 'ortho'})

    node_attributes = {'fontname': ' ',  # use website default
                       'fontsize': '10.5px'  # fontsize unfortunately must be set
                       }

    tables: List[Tuple[Optional[str], str, List[str]]]
    fk_relationships: FKRelationship

    if db.dialect.name == 'postgresql':
        from mara_db import postgres_helper
        tables = postgres_helper.list_tables_and_columns(db, schemas)
        fk_relationships = postgres_helper.list_fk_constraints(db)

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
        separator = '  '
        graph.node(shape='plain', name=f'{schema_name}__{table_name}',
                   label=''.join(['<',
                                  f""" <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="1" BGCOLOR="{schema_color(schema_name)}"><TR><TD ALIGN="LEFT"><U><B>""",
                                  f'{schema_name}.{table_name}' if len(schemas) > 1 else table_name,
                                  """</B></U></TD></TR>""", ''.join(
                           [f'<TR><TD ALIGN="LEFT" >{separator}{c}{separator}</TD></TR>' for c in columns]),
                                  """"</TABLE> """,

                                  '>']), _attributes=node_attributes)
    shown_tables = [f'{s}__{t}' for (s, t, _) in tables]
    for rel in fk_relationships:
        # NOTE: currently cross-schema relationships are retrieved but not displayed
        source_name = f'{rel.source_schema}__{rel.source_table}'
        target_name = f'{rel.target_schema}__{rel.target_table}'
        if source_name in shown_tables and target_name in shown_tables:
            graph.edge(source_name, target_name)
    return graph.pipe('svg').decode('utf-8')


@mara_db.route('/svg/<string:db_alias>/<string:schemas>')
@acl.require_permission(acl_resource)
def get_svg(db_alias: str, schemas: str):
    """Shows a chart of the tables and FK relationships in a given database and schema list"""
    if db_alias not in config.databases():
        return response.Response(status_code=400, title=f'unkown database {db_alias}',
                                 html=f'Error, database {db_alias} is unknown')

    db = config.databases()[db_alias]
    return draw_schema(db, schemas.split('|'))


@mara_db.route('/<string:db_alias>')
@acl.require_permission(acl_resource)
def index_page(db_alias: str):
    """Shows a page to let the user pick some schemas and see the tables and FK"""
    if db_alias not in config.databases():
        return response.Response(status_code=400, title=f'unkown database {db_alias}',
                                 html=[bootstrap.card(body=_.p(style='color:red')[
                                     'The database alias ',
                                     _.strong()[db_alias],
                                     ' is unknown'
                                 ])])

    db = config.databases()[db_alias]
    if db.dialect.name == 'postgresql':
        from mara_db import postgres_helper
        available_schemas = postgres_helper.list_schemas(db)
        return response.Response(title=f'Schemas of {db_alias}',
                                 html=[''.join(['<script src="',
                                                flask.url_for('mara_db.static', filename='mara_db.js'),
                                                '">', '</script>']), bootstrap.card(body=''.join([
                                     f'<input type="checkbox" value="{s}"> {s} ' for s in available_schemas
                                 ]))])

    return response.Response(status_code=400, title=f'unkown database {db_alias}',
                             html=[bootstrap.card(body=_.p(style='color:red')[
                                 'The database alias ',
                                 _.strong()[db_alias],
                                 ' is of type ',
                                 _.strong()[db.dialect.name],
                                 ' which is not supported'
                             ])])
