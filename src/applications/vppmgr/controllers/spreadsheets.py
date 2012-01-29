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
    form = SQLFORM(db.vpp_order, vpp_order, readonly=True)
    user_codes = db((db.vpp_code.vpp_order==vpp_order.id) &
        (db.auth_user.id==db.vpp_code.owner)).select(
        db.vpp_code.id, db.vpp_code.code, db.vpp_code.status, db.vpp_code.device, db.auth_user.email,
        orderby=[db.auth_user.email, db.vpp_code.status])
    no_user_codes = db((db.vpp_code.vpp_order==vpp_order.id) &
        (db.vpp_code.owner==None)).select(
        db.vpp_code.id, db.vpp_code.code, db.vpp_code.status, db.vpp_code.device, db.vpp_code.owner,
        orderby=db.vpp_code.status)
    code_table = 'No codes were found in this spreadsheet'
    if len(user_codes) + len(no_user_codes) > 0:
        code_table = SQLTABLE(user_codes, headers='fieldname:capitalize')
        no_user_code_table = SQLTABLE(no_user_codes, headers='fieldname:capitalize')
        no_user_rows = no_user_code_table.elements('tr')
        if len(no_user_rows) > 0:
            tbody = code_table.elements('tbody')
            if len(tbody) > 0:
                tbody[0].append(no_user_rows)
            else:
                code_table = no_user_code_table    
    return dict(vpp_order=vpp_order, form=form, code_table=code_table)

def assign_apps():
    if request.env.request_method == 'POST': # postback
        n = 0
        for k in request.post_vars.iterkeys():
            m = re.match(r'order_(\d+)', k)
            if m is not None:
                vpp_order_id = int(m.group(1))
                vpp_order = db.vpp_order[vpp_order_id]
                app_id = int(request.post_vars[k])
                curr_app_id = 0
                if vpp_order.app is not None:
                    curr_app_id = int(vpp_order.app)
                if vpp_order is not None and app_id != curr_app_id:
                    vpp_order.update_record(app=app_id)
                    n += 1
        response.flash = 'Updated %d spreadsheet records' % (n)
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
    vpp_orders = vpp_manager.read_orders([ vpp_order.spreadsheet_name ])
    updates = vpp_manager.update_orders(vpp_orders)
    fmt = 'Created %d and updated %d spreadsheet records (%d codes redeemed, %d reserved, %d pending, %d unused)'
    session.flash = fmt % (updates['created'], updates['updated'],
        updates['redeemed'], updates['reserved'], updates['pending'], updates['unused'])
    redirect(URL('index'))

# GET /vppmgr/spreadsheets/import_all    
def import_all():
    updates = vpp_manager.populate_order_table()
    fmt = 'Created %d and updated %d spreadsheet records (%d codes redeemed, %d reserved, %d pending, %d unused)'
    session.flash = fmt % (updates['created'], updates['updated'],
        updates['redeemed'], updates['reserved'], updates['pending'], updates['unused'])
    redirect(URL('index'))
