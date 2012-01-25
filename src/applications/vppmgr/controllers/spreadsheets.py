# -*- coding: utf-8 -*-
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
    ss_names = vpp_manager.get_vpp_spreadsheets()
    ss_rows = vpp_manager.select_spreadsheets(ss_names)
    app_rows = vpp_manager.select_apps()
    return dict(spreadsheets=ss_rows, apps=app_rows)        

# GET /vppmgr/spreadsheets/import_one/1
def import_one():
    ss_id = request.args(0)
    ss = None
    if ss_id is not None:
        ss = db(db.spreadsheet.id == ss_id).select().first()
    if ss is None:
        raise HTTP(404)
    vpp_orders = vpp_manager.read_vpp_orders([ ss['spreadsheet_name'] ])
    updates = vpp_manager.update_vpp_orders(vpp_orders)
    return dict(updates=updates)

# GET /vppmgr/spreadsheets/import_all    
def import_all():
    updates = vpp_manager.populate_vpp_order_table()
    return dict(updates=updates)
    
def clear_apps():
    db(db.vpp_order).update(product=None)
    response.flash = 'All apps cleared'
    redirect('index')
    