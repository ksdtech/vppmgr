# -*- coding: utf-8 -*-
import re

def _find_order():
    vpp_order = db.vpp_order(request.args(0))
    if vpp_order is None:
         raise HTTP(404)
    return vpp_order

def index():
    order_rows = vpp_manager.select_orders(request.vars['update'] == '1')
    return dict(spreadsheets=order_rows)        
    
def show():
    vpp_order = _find_order()
    return dict(form=SQLFORM(db.vpp_order, vpp_order, readonly=True))

def assign_apps():
    if request.env.request_method == 'POST': # postback
        n = 0
        for k in request.post_vars.iterkeys():
            m = re.match(r'order_(\d+)', k)
            if m is not None:
                vpp_order_id = int(m.group(1))
                vpp_order = db.vpp_order[order_id]
                app_id = int(request.post_vars[k])
                if vpp_order is not None and int(vpp_order.app) != app_id:
                    vpp_order.update_record(app=app_id)
                    n += 1
        response.flash = '%d spreadsheet records were updated' % (n)
    order_rows = vpp_manager.select_orders()
    app_rows = vpp_manager.select_apps()
    return dict(spreadsheets=order_rows, apps=app_rows)        

def clear_apps():
    db(db.vpp_order).update(app=None)
    session.flash = 'All app assignments were cleared'
    redirect(URL('assign_apps'))

# GET /vppmgr/spreadsheets/import_one/1
def import_one():
    vpp_order = _find_order()
    vpp_orders = vpp_manager.read_orders([ vpp_order['spreadsheet_name'] ])
    updates = vpp_manager.update_orders(vpp_orders)
    session.flash = str(updates)
    redirect(URL('index'))

# GET /vppmgr/spreadsheets/import_all    
def import_all():
    updates = vpp_manager.populate_order_table()
    session.flash = str(updates)
    redirect(URL('index'))
