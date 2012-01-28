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

db.define_table('app_group',
    Field('name', 'string',
        label=T('Name')),
    format='%(name)s',
    migrate=settings.migrate)
    
# for case-insensitive ordering with compute fields
def upcase_field(r, other_field):
    if r[other_field] is None:
        return None
    return r[other_field].upper()

# See http://web2py.com/books/default/chapter/29/6 on list:reference usage
# app
db.define_table('app',
    Field('name', 'string',
        label=T('Name'), unique=True),
    Field('name_nocase', 'string',
        label=T('Name Nocase'), compute=lambda r: upcase_field(r, 'name')),
    Field('app_store_id', 'string',
        label=T('AppStore ID'), unique=True),
    Field('app_store_link', 'string',
        label=T('AppStore Link'), unique=True),
    Field('price', 'string',
        label=T('Price')),
    Field('groups', 'list:reference app_group'),
    Field('created_on', 'datetime', default=request.now,
        label=T('Created On'), writable=False, readable=False),
    Field('modified_on', 'datetime', default=request.now,
        label=T('Modified On'), writable=False, readable=False,
        update=request.now),
    format='%(name)s',
    migrate=settings.migrate)
    
# iOS device
db.define_table('device',
    Field('name', 'string',
        label=T('Name'), unique=True),
    Field('asset_number', 'string',
        label=T('Asset Number')), # unique=True),
    Field('serial_number', 'string',
        label=T('Serial Number')), # unique=True),
    Field('apple_device_id', 'string',
        label=T('Apple Device ID')), # unique=True),
    Field('location', 'string',
        label=T('Location')),
    Field('room', 'string',
        label=T('Room')),
    Field('owner', db.auth_user),
    Field('created_on', 'datetime', default=request.now,
        label=T('Created On'), writable=False, readable=False),
    Field('modified_on', 'datetime', default=request.now,
        label=T('Modified On'), writable=False, readable=False,
        update=request.now),
    format='%(name)s',
    migrate=settings.migrate)
    
# VPP order
db.define_table('vpp_order',
    Field('spreadsheet_name', 'string',
        label=T('Spreadsheet Name'), unique=True),
    Field('spreadsheet_name_nocase', 'string',
        label=T('Spreadsheet Nocase'), compute=lambda r: upcase_field(r, 'spreadsheet_name')),
    Field('order_number', 'string',
        label=T('Order Number')), # unique=True),
    Field('product_name', 'string',
        label=T('Product Name')),
    Field('product_name_nocase', 'string',
        label=T('Product Nocase'), compute=lambda r: upcase_field(r, 'product_name')),
    Field('app', db.app),
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
        label=T('Code'), unique=True),
    Field('app_store_link', 'string',
        label=T('App Store Link'), unique=True),
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
    Field('recipient', 'string',
        label=T('Recipient')),
    Field('subject', 'string',
        label=T('Subject')),
    Field('body', 'text',
        label=T('Body')),
    Field('apps', 'list:reference app',
        label=T('apps')),
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
vpp_manager=VppManager(db, app_settings, mail)

# Populate newly created database from vppusers.csv
# and from Google spreadsheets

if db(db.auth_user).isempty():
    vpp_manager.populate_user_table()
    
if db(db.device).isempty():
    vpp_manager.populate_device_table()

if db(db.app).isempty():
    vpp_manager.populate_app_table()

if db(db.vpp_order).isempty():
    vpp_manager.populate_order_table()

