# -*- coding: utf-8 -*-
from import_vpp import read_products
from update_vpp import update_products

### required - do no delete
def user(): return dict(form=auth())
def download(): return response.download(request,db)
def call(): return service()
### end requires

def index():
    return dict()

def import_all():
    email, password = app_settings.email_login.split(':')
    products = read_products(email, password, app_settings.product_ss_name)
    updates = update_products(db, settings, products)
    return dict(updates=updates)
