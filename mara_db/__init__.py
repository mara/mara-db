def MARA_CONFIG_MODULES():
    from mara_db import config
    return [config]


def MARA_NAVIGATION_ENTRY_FNS():
    from mara_db import views
    return [views.navigation_entry]


def MARA_ACL_RESOURCES():
    from mara_db import views
    return [views.acl_resource]


def MARA_FLASK_BLUEPRINTS():
    from mara_db import views
    return [views.blueprint]


def MARA_CLICK_COMMANDS():
    from mara_db import cli
    return [cli.migrate]
