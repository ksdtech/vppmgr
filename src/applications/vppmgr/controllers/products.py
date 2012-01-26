# -*- coding: utf-8 -*-

def index():
    group_id = request.vars['group']
    group_name = None
    app_rows = vpp_manager.select_apps(group_id)
    group_rows = vpp_manager.select_groups()
    if group_id is not None:
        group_names = [g.name for g in group_rows if g.id==int(group_id)]
        if len(group_names) > 0:
            group_name = group_names[0]
        else:
            group_id = None
    return dict(apps=app_rows, groups=group_rows, group=group_id, group_name=group_name)

def import_all():
    updates = vpp_manager.populate_product_table()
    request.flash = "Updated %d free and %d vpp apps" % (updates['free'], updates['vpp'])
    redirect('index')
