# -*- coding: utf-8 -*-
from import_vpp import get_spreadsheets_in_collection, read_vpp_orders
from update_vpp import update_vpp_orders

def index():
    email, password = app_settings.email_login.split(':')
    ss_names = get_spreadsheets_in_collection(email, password, app_settings.vpp_coll_name)
    return dict(spreadsheets=ss_names)
    
def import_one():
    ss_name = request.vars['ss_name']
    if ss_name is None:
        raise HTTP(404)
    email, password = app_settings.email_login.split(':')
    vpp_orders = read_vpp_orders_vpp_spreadsheets(email, password, [ ss_name ])
    updates = update_vpp_orders(db, settings, vpp_orders)
    return dict(updates=updates)
    
def import_all():
    email, password = app_settings.email_login.split(':')
    ss_names = get_spreadsheets_in_collection(email, password, app_settings.vpp_coll_name)
    vpp_orders = read_vpp_orders_vpp_spreadsheets(email, password, ss_names)
    updates = update_vpp_orders(db, settings, vpp_orders)
    return dict(updates=updates)
