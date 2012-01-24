# -*- coding: utf-8 -*-
from import_vpp import read_products
from update_vpp import select_apps, update_products

def index():
    app_rows = select_apps(db)
    return dict(apps=app_rows)

def import_all():
    email, password = app_settings.email_login.split(':')
    products = read_products(email, password, app_settings.product_ss_name)
    updates = update_products(db, settings, products)
    request.flash = "Updated %d free and %d vpp apps" % (updates['free'], updates['vpp'])
    redirect('index')
