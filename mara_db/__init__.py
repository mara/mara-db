from mara_db import config, views

MARA_CONFIG_MODULES = [config]

MARA_NAVIGATION_ENTRY_FNS = [views.navigation_entry]

MARA_ACL_RESOURCES = [views.acl_resource]

MARA_FLASK_BLUEPRINTS = [views.blueprint]
