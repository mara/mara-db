"""DB schema visualization"""

import functools
from typing import List, NamedTuple, Optional, Tuple

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


def navigation_entry():
    return navigation.NavigationEntry(
        label='DB Schema', uri_fn=lambda: flask.url_for('mara_db.index_page', db_alias=config.mara_db_alias()),
        icon='star',
        description='Data base schemas',
        children=[navigation.NavigationEntry(label=db_alias, icon='database',
                                             description=f'The schema of the {db_alias} db',
                                             uri_fn=functools.partial(
                                                 lambda: flask.url_for('mara_db.index_page', db_alias=db_alias)))
                  for db_alias in config.databases().keys()]
    )


def draw_schema(db: engine.Engine, schema: str = None) -> str:
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
        tables = postgres_helper.list_tables_and_columns(db, schema)
        fk_relationships = postgres_helper.list_fk_constraints(db)
    for schema_name, table_name, columns in tables:
        # graph.node(name=table_name, label='<ol><li>' + table_name + '</ol></li>', _attributes=node_attributes)
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
        graph.node(shape='plain', name=table_name,
                   label=''.join(['<',
                                  """ <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="1" BGCOLOR="#bbffcc"><TR><TD ALIGN="LEFT"><U><B>""",
                                  table_name,
                                  """</B></U></TD></TR>""", ''.join(
                           [f'<TR><TD ALIGN="LEFT" >{separator}{c}{separator}</TD></TR>' for c in columns]),
                                  """"</TABLE> """,

                                  '>']), _attributes=node_attributes)

    schema_tables_only = {(s, t) for (s, t, _) in tables}
    for rel in fk_relationships:
        # NOTE: currently cross-schema relationships are retrieved but not displayed
        if (schema, rel.source_table) in schema_tables_only and (schema, rel.target_table) in schema_tables_only:
            graph.edge(rel.source_table, rel.target_table)
    return graph.pipe('svg').decode('utf-8')


@mara_db.route('/<string:db_alias>', defaults={'schema': None})
@mara_db.route('/<string:db_alias>/<string:schema>')
@acl.require_permission(acl_resource)
def index_page(db_alias: str, schema: str = None):
    """Shows a chart of the tables and FK relationships in a given database (and schema, if present)"""
    if db_alias not in config.databases():
        return response.Response(status_code=400, title=f'unkown database {db_alias}',
                                 html=[bootstrap.card(body=_.p(style='color:red')[
                                     'The database alias ',
                                     _.strong()[db_alias],
                                     ' is unknown'
                                 ])])

    db = config.databases()[db_alias]
    return response.Response(
        title='DB Schemas',
        html=[
            bootstrap.card(header_left='Schemas',
                           body=[_.p()['Database object of kind:'], repr(db)]),
            bootstrap.card(body=[
                _.h1()['Schema: ', schema],
                draw_schema(db, schema)
            ])
        ])
