"""DB schema visualization"""

import flask
import graphviz
from typing import NamedTuple, Optional, Tuple

from mara_db import config
from mara_page import acl, navigation, response, bootstrap, _
from sqlalchemy import engine


FKRelationship = NamedTuple("FKRelationship", [('source_schema', Optional[str]), ('source_table', str), ('target_schema', Optional[str]), ('target_table', str)])


mara_db = flask.Blueprint('mara_db', __name__, static_folder='static', url_prefix='/db')

acl_resource = acl.AclResource(name='DB')

navigation_entry = navigation.NavigationEntry(
    label='DB Schema', uri_fn=lambda: flask.url_for('mara_db.index_page', db_alias=config.mara_db_alias()), icon='star',
    rank=200,
    description='Data base schemas')


def draw_schema(db: engine.Engine, schema: str=None) -> str:
    graph = graphviz.Digraph(graph_attr={'rankdir': 'TD',
                                         'ranksep': '0.25',
                                         'nodesep': '0.1',
                                         #'ratio': 'compress',
                                         'size': '500,500'})
    node_attributes = {'fontname': ' ',  # use website default
                       'fontsize': '10.5px'  # fontsize unfortunately must be set
                       }

    tables: Tuple[Optional[str], str]
    fk_relationships: FKRelationship

    if db.dialect.name == 'postgresql':
        from mara_db import postgres_helper
        tables = [(schema, table_name) for table_name in postgres_helper.list_tables(db, schema)]
        fk_relationships = postgres_helper.list_fk_constraints(db)

    for schema_name, table_name in tables:
        graph.node(name=table_name, label=table_name, _attributes=node_attributes)
    for rel in fk_relationships:
        # NOTE: currently cross-schema relationships are retrieved but not displayed
        if (schema, rel.source_table) in tables and (schema, rel.target_table) in tables:
            graph.edge(rel.source_table, rel.target_table)
    return graph.pipe('svg').decode('utf-8')


@mara_db.route('/<string:db_alias>', defaults={'schema': None})
@mara_db.route('/<string:db_alias>/<string:schema>')
@acl.require_permission(acl_resource)
def index_page(db_alias: str, schema: str=None):
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
                _.h1()[schema],
                draw_schema(db, schema)
            ])
        ])
