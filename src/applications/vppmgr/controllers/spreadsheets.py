# -*- coding: utf-8 -*-
import re

def index():
    if request.env.request_method == 'POST': # postback
        n = 0
        for k in request.post_vars.iterkeys():
            m = re.match(r'order_(\d+)', k)
            if m is not None:
                order_id = int(m.group(1))
                app_id = int(request.post_vars[k])
                ss = db.vpp_order[order_id]
                if ss is not None and ss.app != app_id:
                    ss.update_record(app=app_id)
                    n += 1
        response.flash = '%d spreadsheet records updated' % (n)
    spreadsheet_names = vpp_manager.get_vpp_spreadsheets()
    order_rows = vpp_manager.select_orders(spreadsheet_names)
    app_rows = vpp_manager.select_apps()
    return dict(spreadsheets=order_rows, apps=app_rows)        

# GET /vppmgr/spreadsheets/import_one/1
def import_one():
    order_id = request.args(0)
    vpp_order = None
    if order_id is not None:
        vpp_order = db(db.spreadsheet.id == order_id).select(limitby=(0,1)).first()
    if vpp_order is None:
        raise HTTP(404)
    vpp_orders = vpp_manager.read_orders([ vpp_order['spreadsheet_name'] ])
    updates = vpp_manager.update_orders(vpp_orders)
    return dict(updates=updates)

# GET /vppmgr/spreadsheets/import_all    
def import_all():
    updates = vpp_manager.populate_order_table()
    return dict(updates=updates)
    
def clear_apps():
    db(db.vpp_order).update(app=None)
    response.flash = 'All apps cleared'
    redirect('index')
    