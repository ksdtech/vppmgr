#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

# app
db.define_table('product',
    Field('name', type='string',
        label=T('Name')),
    Field('app_store_id', type='string',
        label=T('AppStore ID')),
    Field('app_store_link', type='string',
        label=T('AppStore Link')),
    Field('price', type='string',
        label=T('Price')),
    Field('created_on','datetime', default=request.now,
        label=T('Created On'), writable=False, readable=False),
    Field('modified_on','datetime', default=request.now,
        label=T('Modified On'), writable=False, readable=False,
        update=request.now),
    format='%(name)s %(id)s',
    migrate=settings.migrate)

# iOS device
db.define_table('device',
    Field('name', type='string',
        label=T('Name')),
    Field('asset_number', type='string',
        label=T('Asset Number')),
    Field('serial_number', type='string',
        label=T('Serial Number')),
    Field('location', type='string',
        label=T('Location')),
    Field('owner', db.auth_user),
    Field('created_on','datetime', default=request.now,
        label=T('Created On'), writable=False, readable=False),
    Field('modified_on','datetime', default=request.now,
        label=T('Modified On'), writable=False, readable=False,
        update=request.now),
    format='%(name)s %(id)s',
    migrate=settings.migrate)
    
# VPP order
db.define_table('vpp_order',
    Field('order_number', type='string',
        label=T('Order Number')),
    Field('spreadsheet_name', type='string',
        label=T('Spreadsheet Name')),
    Field('product_name', type='string',
        label=T('Product Name')),
    Field('product', db.product),
    Field('created_on','datetime', default=request.now,
        label=T('Created On'), writable=False, readable=False),
    Field('modified_on','datetime', default=request.now,
        label=T('Modified On'), writable=False, readable=False,
        update=request.now),
    format='%(spreadsheet_name)s %(id)s',
    migrate=settings.migrate)

# VPP redemption code
db.define_table('vpp_code',
    Field('code', type='string',
        label=T('Code')),
    Field('status', type='string', default='Unused', 
        requires=IS_IN_SET(['Unused', 'Redeemed', 'Reserved']),
        label=T('Status')),
    Field('vpp_order', db.vpp_order),
    Field('device', db.device),
    Field('owner', db.auth_user),
    Field('created_on','datetime', default=request.now,
        label=T('Created On'), writable=False, readable=False),
    Field('modified_on','datetime', default=request.now,
        label=T('Modified On'), writable=False, readable=False,
        update=request.now),
    format='%(code)s',
    migrate=settings.migrate)
