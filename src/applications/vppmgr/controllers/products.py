# -*- coding: utf-8 -*-
from import_vpp import read_products
from update_vpp import update_products

def index():
    return dict()

def import_all():
    email, password = app_settings.email_login.split(':')
    products = read_products(email, password, app_settings.product_ss_name)
    updates = update_products(db, settings, products)
    return dict(updates=updates)
