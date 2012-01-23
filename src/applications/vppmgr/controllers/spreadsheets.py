# -*- coding: utf-8 -*-
from import_vpp import get_spreadsheets_in_collection, read_vpp_orders
from update_vpp import select_spreadsheets, select_apps, update_vpp_orders
import re

def index():
    if request.env.request_method == 'POST': # postback
        n = 0
        for k in request.post_vars.iterkeys():
            m = re.match(r'sel_(\d+)', k)
            if m:
                ss_id = int(m.group(1))
                product_id = int(request.post_vars[k])
                ss = db.vpp_order[ss_id]
                if ss is not None and ss.product != product_id:
                    ss.update_record(product=product_id)
                    n += 1
        response.flash = '%d spreadsheet records updated' % (n)
    email, password = app_settings.email_login.split(':')
    ss_names = get_spreadsheets_in_collection(email, password, app_settings.vpp_coll_name)
    ss_rows = select_spreadsheets(db, ss_names)
    app_rows = select_apps(db)
    return dict(spreadsheets=ss_rows, apps=app_rows)        

# GET /vppmgr/spreadsheets/import_one/1
def import_one():
    ss_id = request.args(0)
    ss = None
    if ss_id is not None:
        ss = db(db.spreadsheet.id == ss_id).select().first()
    if ss is None:
        raise HTTP(404)
    email, password = app_settings.email_login.split(':')
    vpp_orders = read_vpp_orders(email, password, [ ss['spreadsheet_name'] ])
    updates = update_vpp_orders(db, settings, vpp_orders)
    return dict(updates=updates)

# GET /vppmgr/spreadsheets/import_all    
def import_all():
    email, password = app_settings.email_login.split(':')
    ss_names = get_spreadsheets_in_collection(email, password, app_settings.vpp_coll_name)
    vpp_orders = read_vpp_orders(email, password, ss_names)
    updates = update_vpp_orders(db, settings, vpp_orders)
    return dict(updates=updates)
    
def clear_apps():
    db(db.vpp_order.id != 0).update(product=None)
    response.flash = 'All apps cleared'
    redirect('index')
    