# -*- coding: utf-8 -*-

def index():
    devices = db().select(db.device.ALL, orderby=[db.device.numeric_order, db.device.name])
    return dict(devices=devices)
    
def import_all():
    updates = vpp_manager.populate_device_table()
    session.flash = "Created %d and updated %d devices" % (updates['created'], updates['updated'])
    redirect(URL('index'))
