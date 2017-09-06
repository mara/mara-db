"""DB schema visualization"""

import flask
import graphviz

from mara_db import config
from mara_page import acl, navigation, response, bootstrap, _
from sqlalchemy import MetaData, engine



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
    # TODO this does not manage Postgres table inheritance but could be used for other engines, see vendor/project-a/dwh-package/src/ProjectA/Zed/Dwh/Component/Gui/Db.php for reference implementation
    meta = MetaData()
    meta.reflect(bind=db, schema=schema)
    graph.node(name='foo', label='foo', _attributes=node_attributes)
    graph.node(name='bar', label='bar', _attributes=node_attributes)
    for name, table in meta.tables.items():
        graph.node(name=name, label=name[1 + len(schema) if schema is not None else 0:], _attributes=node_attributes)

#    graph.edge('foo', 'bar')
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
            bootstrap.card(body=_.h1(style='color:blue')[
                'foo',
                draw_schema(db, schema)
            ])
        ])
