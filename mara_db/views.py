"""DB schema visualization"""

import flask
from mara_db import config
from mara_page import acl, navigation, response, bootstrap,_
import graphviz

mara_db = flask.Blueprint('mara_db', __name__, static_folder='static', url_prefix='/db')

acl_resource = acl.AclResource(name='DB')

navigation_entry = navigation.NavigationEntry(
    label='DB Schema', uri_fn=lambda: flask.url_for('mara_db.index_page', db_alias=config.mara_db_alias()), icon='star',
    rank=200,
    description='Data base schemas')

def draw_schema() -> str:
    graph = graphviz.Digraph(graph_attr={'rankdir': 'TD', 'ranksep': '0.25', 'nodesep': '0.1'})
    node_attributes = {'fontname': ' ',  # use website default
                       'fontsize': '10.5px'  # fontsize unfortunately must be set
                       }

    graph.node(name='foo', label='foo', _attributes=node_attributes)
    graph.node(name='bar', label='bar', _attributes=node_attributes)
    graph.edge('foo', 'bar')
    return graph.pipe('svg').decode('utf-8')


@mara_db.route('/<string:db_alias>')
@acl.require_permission(acl_resource)
def index_page(db_alias: str):
    db = config.databases()[db_alias]
    return response.Response(
        title='DB Schemas',
        html=[
            bootstrap.card(header_left='Schemas',
                           body=repr(db)),
            bootstrap.card(body=_.h1(style='color:blue')[
                'foo',
                draw_schema()
            ])
        ])
