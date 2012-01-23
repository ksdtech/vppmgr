# -*- coding: utf-8 -*-
from import_vpp import get_spreadsheets_in_collection, import_google_vpp_spreadsheets
from update_vpp import update_vpp_codes

### required - do no delete
def user(): return dict(form=auth())
def download(): return response.download(request,db)
def call(): return service()
### end requires

def index():
    return dict()

def error():
    return dict()
    
def display_form():
    record = db.vpp_order(request.args(0)) or redirect(URL('index'))
    form = SQLFORM(db.vpp_order, record)
    if form.process().accepted:
        response.flash = 'form accepted'
    elif form.errors:
        response.flash = 'form has errors'
    return dict(form=form)

def spreadsheets():
    email, password = app_settings.email_login.split(':')
    ss_names = get_spreadsheets_in_collection(email, password, app_settings.vpp_coll_name)
    return dict(spreadsheets=ss_names)
    
def import_one():
    ss_name = request.vars['ss_name']
    if ss_name is None:
        raise HTTP(404)
    email, password = app_settings.email_login.split(':')
    vpp_orders = import_google_vpp_spreadsheets(email, password, [ ss_name ])
    updates = update_vpp_codes(db, settings, vpp_orders)
    return dict(updates=updates)
    
def import_all():
    email, password = app_settings.email_login.split(':')
    ss_names = get_spreadsheets_in_collection(email, password, app_settings.vpp_coll_name)
    vpp_orders = import_google_vpp_spreadsheets(email, password, ss_names)
    updates = update_vpp_codes(db, settings, vpp_orders)
    return dict(updates=updates)
