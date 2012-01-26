import gdata.docs.data
import gdata.docs.client
import gdata.spreadsheet
import gdata.spreadsheet.service
import csv
import re
from urllib import quote_plus

class VppManager:
    def __init__(self, db, app_settings, mailer):
        self.db = db
        self.settings = app_settings
        self.mailer = mailer

    # private utilities
    def _find_spreadsheet(self, ss_feed, name):
        for entry in ss_feed.entry:
            # print entry.title.text
            if entry.title.text == name:
                return entry.id.text.rsplit('/', 1)[1]
        return None

    # private gdata login operations
    def _docs_client(self):
        email, password = self.settings.email_login.split(':')
        gd_client = gdata.docs.client.DocsClient(source='vpp-app.kentfieldschools.org.1')
        gd_client.ClientLogin(email, password, gd_client.source)
        return gd_client
        
    def _ss_client(self):
        email, password = self.settings.email_login.split(':')
        ss_client = gdata.spreadsheet.service.SpreadsheetsService()
        ss_client.email = email
        ss_client.password = password
        ss_client.source = 'vpp-app.kentfieldschools.org.1'
        ss_client.ProgrammaticLogin()
        return ss_client
    
    # gdata private read operations
    def _read_vpp_data(self, ss_client, ss_name, ss_key):
        vpp_order = dict()
        vpp_order['spreadsheet_name'] = ss_name
        vpp_order['codes'] = [ ]
        ss_ws_feed = ss_client.GetWorksheetsFeed(ss_key)
        ws_entry = ss_ws_feed.entry[0]
        ws_key = ws_entry.id.text.rsplit('/', 1)[1]
        row_count = ws_entry.row_count.text
        # print "worksheet id: %s, %s rows" % (ws_key, row_count)
        cell_feed = ss_client.GetCellsFeed(ss_key, ws_key)
        # print cell_feed.ToString()
        for i, entry in enumerate(cell_feed.entry):
            # Order Number: Row 2, Column 3 
            # Product Name: Row 3, Column 3
            # Number of Codes: Row 5, Column 3
            # Rows 11 - 11+n:
            #  Redemption Link: Column 3
            #  Status: Column 4 (redeemed, reserved, etc)
            #  Device Name: Column 5
            #  Device Group: Column 6
            row = int(entry.cell.row)
            col = int(entry.cell.col)
            if row == 2 and col == 3:
                vpp_order['order_number'] = entry.cell.text
            elif row == 3 and col == 3:
                vpp_order['product_name'] = entry.cell.text
            elif row == 5 and col == 3:
                vpp_order['code_count'] = int(entry.cell.text)
            elif row >= 11:
                if col == 1:
                    vpp_order['codes'].append(dict())
                    vpp_order['codes'][row-11]['code'] = entry.cell.text
                elif col == 3:
                    vpp_order['codes'][row-11]['link'] = entry.cell.text
                elif col == 4:
                    vpp_order['codes'][row-11]['status'] = entry.cell.text
                elif col == 5:
                    vpp_order['codes'][row-11]['device_name'] = entry.cell.text
                elif col == 6:
                    vpp_order['codes'][row-11]['user_email'] = entry.cell.text
        return vpp_order

    def _read_product_data(self, gd_client, ss_name, ss_key):
        products = dict()
        ss_ws_feed = gd_client.GetWorksheetsFeed(ss_key)
        ws_entry = ss_ws_feed.entry[0]
        ws_key = ws_entry.id.text.rsplit('/', 1)[1]
        row_count = ws_entry.row_count.text
        # print "worksheet id: %s, %s rows" % (ws_key, row_count)
        query = gdata.spreadsheet.service.CellQuery()
        query['min-col'] = '1'
        query['max-col'] = '12'
        cell_feed = gd_client.GetCellsFeed(ss_key, ws_key, query=query)
        name = None
        link = None
        price = None
        product_id = None
        groups = [ 'Group %d' % (i+1) for i in range(7) ]
        for i, entry in enumerate(cell_feed.entry):
            row = int(entry.cell.row)
            col = int(entry.cell.col)
            # print "R%dC%d: %s" % (row, col, entry.cell.text)
            if row == 1 and col >= 6 and col <= 12:
                # Header Row, group names
                groups[col-6] = entry.cell.text
            elif row >= 3:
                # Product Rows, 3 to n
                # Product Name: Column 1
                # App Store Link: Column 2
                # List Price: Column 3
                if col == 1:
                    name = entry.cell.text
                    link = None
                    price = None
                    product_id = None
                elif col == 2:
                    link = entry.cell.text
                elif col == 3:
                    price = entry.cell.text[1:] # strip dollar sign
                    if price == '' or price == '0':
                        price = '0.00'
                    m = re.search(r'\/id(\d+)\?', link) # extract id number
                    if m is not None:
                        product_id = m.group(1)
                        products[product_id] = dict()
                        products[product_id]['app_store_id'] = product_id
                        products[product_id]['app_store_link'] = link
                        products[product_id]['name'] = name
                        products[product_id]['price'] = price
                        products[product_id]['groups'] = [ ]
                elif product_id is not None and col >= 6 and col <= 12 and len(entry.cell.text) > 0:
                    products[product_id]['groups'].append(groups[col-6])
        return products
    
    def _update_vpp_cells_in_row(self, ss_key, ws_key, row, status, user, device):
        e4 = ss_client.UpdateCell(row=row, col=4, inputValue=status, 
            key=ss_key, wksht_id=ws_key)
        if not isinstance(e4, gdata.spreadsheet.SpreadsheetsCell):
            return False
        e5 = ss_client.UpdateCell(row=row, col=5, inputValue=device, 
            key=ss_key, wksht_id=ws_key)
        if not isinstance(e4, gdata.spreadsheet.SpreadsheetsCell):
            return False
        e6 = ss_client.UpdateCell(row=row, col=6, inputValue=user, 
            key=ss_key, wksht_id=ws_key)
        if not isinstance(e4, gdata.spreadsheet.SpreadsheetsCell):
            return False
        return True
    
    # gdata private update operations
    def _update_vpp_code_in_spreadsheet(self, ss_client, ss_name, ss_key, code, status, user, device):
        ss_ws_feed = ss_client.GetWorksheetsFeed(ss_key)
        ws_entry = ss_ws_feed.entry[0]
        ws_key = ws_entry.id.text.rsplit('/', 1)[1]
        row_count = ws_entry.row_count.text
        # print "worksheet id: %s, %s rows" % (ws_key, row_count)
        query = gdata.spreadsheet.service.CellQuery()
        query['min-row'] = '11'        
        cell_feed = ss_client.GetCellsFeed(ss_key, ws_key, query=query)
        # print cell_feed.ToString()
        success = False
        for i, entry in enumerate(cell_feed.entry):
            # Rows 11 - 11+n:
            #  Redemption Link: Column 3
            #  Status: Column 4 (redeemed, reserved, etc)
            #  Device Name: Column 5
            #  Device Group: Column 6
            row = int(entry.cell.row)
            col = int(entry.cell.col)
            if row >= 11 and col == 1:
                found_code = entry.cell.text
                if found_code == code:
                    success = self._update_vpp_cells_in_row(ss_key, ws_key, row, status, user, device)
                    break
        return success
        
    def _next_pending_vpp_code(self, ss_client, product, user, device):
        db = self.db
        vpp_code = db(db.vpp_code.status=='Unused' & db.vpp_code.vpp_order.product==product_id).select().first()
        if vpp_code is not None:
            ss_feed = ss_client.GetSpreadsheetsFeed()
            ss_name = vpp_code.vpp_order.spreadsheet_name
            ss_key = self._find_spreadsheet(ss_feed, ss_name)
            if ss_key is not None:
                if _update_vpp_code_in_spreadsheet(ss_client, ss_name, ss_key, vpp_code.code, 'Pending', user, device):
                    vpp_code.update(status='Pending')
                    return vpp_code
        return None
        
    # gdata public read opearations
    def get_vpp_spreadsheets(self, coll_name=None):
        gd_client = self._docs_client()
        if coll_name is None:
            coll_name = self.settings.vpp_coll_name
        folder_feed = gd_client.GetDocList(uri='/feeds/default/private/full/-/folder?title=%s&title-exact=true&max-results=1' % (quote_plus(coll_name)))
        folder = folder_feed.entry[0]
        res_id = folder.resource_id.text
        ss_feed = gd_client.GetDocList(uri='/feeds/default/private/full/%s/contents/-/spreadsheet?showfolders=false' % (res_id))
        ss_titles = [ ]
        for ss_entry in ss_feed.entry:
            title = ss_entry.title.text
            if title[0] != '_':
                ss_titles.append(title)
        ss_titles.sort(key=str.lower)
        return ss_titles

    def read_vpp_orders(self, ss_names):
        results = dict()
        if len(ss_names) > 0:
            ss_client = self._ss_client()
            ss_feed = ss_client.GetSpreadsheetsFeed()
            for ss_name in ss_names:
                ss_key = self._find_spreadsheet(ss_feed, ss_name)
                if ss_key is None:
                    raise HTTP(500)
                    results[ss_name] = dict()
                else:
                    results[ss_name] = self._read_vpp_data(ss_client, ss_name, ss_key)
        return results

    def read_products(self, ss_name=None):
        results = dict()
        ss_client = self._ss_client()
        ss_feed = ss_client.GetSpreadsheetsFeed()
        if ss_name is None:
            ss_name = self.settings.product_ss_name
        ss_key = self._find_spreadsheet(ss_feed, ss_name)
        if ss_key is None:
            raise HTTP(500)
        else:
            results = self._read_product_data(ss_client, ss_name, ss_key)
        return results    

    # database select operations
    def select_spreadsheets(self, ss_names=None):
        db = self.db
        if ss_names is not None:
            for ss_name in ss_names:
                db.vpp_order.update_or_insert(db.vpp_order.spreadsheet_name == ss_name, spreadsheet_name=ss_name)
        return db().select(db.vpp_order.ALL, orderby=db.vpp_order.spreadsheet_name_nocase)

    def select_apps(self, group=None):
        db = self.db
        scope = None
        if group is not None:
            scope = db(db.product.groups.contains(group))
        else:
            scope = db()
        return scope.select(db.product.ALL, orderby=db.product.name_nocase)

    def select_groups(self):
        db = self.db
        return db().select(db.product_group.ALL, orderby=db.product_group.name)

    # database insert operations
    def populate_user_table(self):
        db = self.db
        user_reader = csv.DictReader(open(self.settings.user_file))
        for row in user_reader:
            email, email_error = db.auth_user.email.validate(row['email'])
            password, password_error = db.auth_user.password.validate(row['password'])
            if email_error is None and password_error is None:
                db.auth_user.insert(email=email, password=password,
                    first_name=row['first_name'],
                    last_name=row['last_name'])
    
    def populate_product_table(self):             
        products = self.read_products()
        return self.update_products(products)

    def populate_vpp_order_table(self):
        ss_names = self.get_vpp_spreadsheets()
        vpp_orders = self.read_vpp_orders(ss_names)
        return self.update_vpp_orders(vpp_orders)

    # email operations
    def queue_and_send_message(self, recipient, device, subject, apps):
        ss_client = self._ss_client()
        products = [ ]
        codes = [ ]
        body_lines = [ ]
        body_lines.append('Here are the links to your redemption codes and')
        body_lines.append('other download links for the apps you requested:')

        for app in apps:
            body_lines.append('')
            body_lines.append('%s:' % (app.name))
            products.append(app.id)
            vpp_code = _next_pending_vpp_code(ss_client, app, recipient, device)
            if vpp_code is not None:
                if vpp_code:
                    codes.append(vpp_code.id)
                    body_lines.append('VPP: %s' % (vpp_code.app_store_link))
                else:
                    body_lines.append('$%s: %s' % (app.price, app.app_store_link))
        body_lines.append('')
        body_lines.append('--App Administrator')            

        subject = 'Please install these apps'
        body = "\n".join(body_lines)
        
        db = self.db
        msg_id = db.invitation.insert(recipient=recipient,
            subject=subject,
            body=body,
            products=products,
            vpp_codes=codes)
        success = self.mailer.send(to=[ recipient ], subject=subject, message=body)
        timestamp = datetime.datetime.now()
        status = 'Sent'
        if not success:
            status = 'Errors: %s' % (self.mailer.error)
        db.invitation(msg_id).update(last_sent_on=timestamp, last_status=status)
        return msg_id

    # database update operations
    def update_vpp_orders(self, vpp_orders):
        db = self.db
        stats = dict(orders=0, redeemed=0, reserved=0, unused=0)
        for ss_name in vpp_orders.iterkeys():
            vpp_order = vpp_orders[ss_name]
            order_number = vpp_order['order_number']
            spreadsheet_name = vpp_order['spreadsheet_name']
            product_name = vpp_order['product_name']
            order = db.vpp_order.update_or_insert(
                db.vpp_order.order_number == order_number and db.vpp_order.product_name == product_name,
                order_number=order_number,
                spreadsheet_name=spreadsheet_name,
                spreadsheet_name_nocase=spreadsheet_name.upper(),
                product_name=product_name,
                product_name_nocase=product_name.upper())
            stats['orders'] += 1
            for vpp_code in vpp_order['codes']:
                device = None
                owner = None
                device_name = vpp_code.get('device_name')
                user_email = vpp_code.get('user_email')
                if user_email is not None:
                    if user_email.find('@') < 0:
                        user_email += '@'
                        user_email += self.settings.domain
                status = vpp_code.get('status')
                if status is None:
                    status = 'Unused'
                    stats['unused'] += 1
                else:
                    status = status.capitalize()
                    if status == 'Redeemed':
                        stats['redeemed'] += 1
                    else:
                        status = 'Reserved'
                        stats['reserved'] += 1         
                    if user_email is None:
                        user_email = self.settings.default_vpp_user
                    owner = db.auth_user.update_or_insert(db.auth_user.email == user_email,
                        email=user_email)
                    if device_name is None:
                        device_name = 'Unknown'
                    device = db.device.update_or_insert(db.device.name == device_name,
                        name=device_name)
                code = vpp_code['code']
                link = vpp_code['link']
                db.vpp_code.update_or_insert(db.vpp_code.code == code,
                    code=code, app_store_link=link, status=status,
                    vpp_order=order,
                    device=device,
                    owner=owner)
        return stats

    def update_products(self, products):
        db = self.db
        stats = dict(free=0, vpp=0)
        for app_store_id in products.iterkeys():
            app = products[app_store_id]
            name = app['name']
            link = app['app_store_link']
            price = app['price']
            groups = [ ]
            for group_name in app['groups']:
                self.db.product_group.update_or_insert(name=group_name)
                groups.append(self.db(self.db.product_group.name == group_name).select().first().id)
            self.db.product.update_or_insert(self.db.product.app_store_id == app_store_id,
                name=name,
                name_nocase=name.upper(),
                app_store_id=app_store_id,
                app_store_link=link,
                groups=groups,
                price=price)
            if price == '0.00':
                stats['free'] += 1
            else:
                stats['vpp'] += 1
        return stats
