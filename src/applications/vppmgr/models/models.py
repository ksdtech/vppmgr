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

db.define_table('product_group',
    Field('name', 'string',
        label=T('Name')),
    format='%(name)s',
    migrate=settings.migrate)

# See http://web2py.com/books/default/chapter/29/6 on list:reference usage
# app
db.define_table('product',
    Field('name', 'string',
        label=T('Name')),
    Field('name_nocase', 'string',
        label=T('Name Nocase')),
    Field('app_store_id', 'string',
        label=T('AppStore ID')),
    Field('app_store_link', 'string',
        label=T('AppStore Link')),
    Field('price', 'string',
        label=T('Price')),
    Field('groups', 'list:reference product_group'),
    Field('created_on', 'datetime', default=request.now,
        label=T('Created On'), writable=False, readable=False),
    Field('modified_on', 'datetime', default=request.now,
        label=T('Modified On'), writable=False, readable=False,
        update=request.now),
    format='%(name)s %(id)s',
    migrate=settings.migrate)
    
# iOS device
db.define_table('device',
    Field('name', 'string',
        label=T('Name')),
    Field('asset_number', 'string',
        label=T('Asset Number')),
    Field('serial_number', 'string',
        label=T('Serial Number')),
    Field('location', 'string',
        label=T('Location')),
    Field('owner', db.auth_user),
    Field('created_on', 'datetime', default=request.now,
        label=T('Created On'), writable=False, readable=False),
    Field('modified_on', 'datetime', default=request.now,
        label=T('Modified On'), writable=False, readable=False,
        update=request.now),
    format='%(name)s %(id)s',
    migrate=settings.migrate)
    
# VPP order
db.define_table('vpp_order',
    Field('order_number', 'string',
        label=T('Order Number')),
    Field('spreadsheet_name', 'string',
        label=T('Spreadsheet Name')),
    Field('spreadsheet_name_nocase', 'string',
        label=T('SS Nocase')),
    Field('product_name', 'string',
        label=T('Product Name')),
    Field('product_name_nocase', 'string',
        label=T('Product Nocase')),
    Field('product', db.product),
    Field('created_on', 'datetime', default=request.now,
        label=T('Created On'), writable=False, readable=False),
    Field('modified_on', 'datetime', default=request.now,
        label=T('Modified On'), writable=False, readable=False,
        update=request.now),
    format='%(spreadsheet_name)s %(id)s',
    migrate=settings.migrate)

# VPP redemption code
db.define_table('vpp_code',
    Field('code', 'string',
        label=T('Code')),
    Field('app_store_link', 'string',
        label=T('App Store Link')),
    Field('status', 'string', default='Unused', 
        requires=IS_IN_SET(['Unused', 'Pending', 'Redeemed', 'Reserved']),
        label=T('Status')),
    Field('vpp_order', db.vpp_order),
    Field('device', db.device),
    Field('owner', db.auth_user),
    Field('created_on', 'datetime', default=request.now,
        label=T('Created On'), writable=False, readable=False),
    Field('modified_on', 'datetime', default=request.now,
        label=T('Modified On'), writable=False, readable=False,
        update=request.now),
    format='%(code)s',
    migrate=settings.migrate)

# Stored email messages
db.define_table('invitation',
    Field('recipient', db.auth_user,
        label=T('Recipient')),
    Field('subject', 'string',
        label=T('Subject')),
    Field('body', 'text',
        label=T('Body')),
    Field('products', 'list:reference product',
        label=T('Products')),
    Field('vpp_codes', 'list:reference vpp_code',
        label=T('VPP Codes')),
    Field('last_sent_on', 'datetime',
        label=T('Last Sent')),
    Field('last_status', 'string',
        label=T('Status')),
    Field('created_on', 'datetime', default=request.now,
        label=T('Created On'), writable=False, readable=False),
    Field('modified_on', 'datetime', default=request.now,
        label=T('Modified On'), writable=False, readable=False,
        update=request.now),
    format='%(recipient)s %(created_on)s %(subject)s',
    migrate=settings.migrate)
    
# Create our manager instance
from vpp_manager import VppManager
vpp_manager=VppManager(db, app_settings, settings.mailer)

# Populate newly created database from vppusers.csv
# and from Google spreadsheets

if db(db.auth_user).isempty():
    vpp_manager.populate_user_table()

if db(db.product).isempty():
    vpp_manager.populate_product_table()

if db(db.vpp_order).isempty():
    vpp_manager.populate_vpp_order_table()

