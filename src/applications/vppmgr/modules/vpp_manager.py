import gdata.docs.data
import gdata.docs.client
import gdata.spreadsheet
import gdata.spreadsheet.service
import csv
from datetime import datetime
import re
from urllib import quote_plus

class VppManager:
    def __init__(self, db, app_settings, mailer):
        self.db = db
        self.settings = app_settings
        self.mailer = mailer

    # private interface    
    # utility methods
    def _find_spreadsheet(self, order_feed, name):
        for entry in order_feed.entry:
            # print entry.title.text
            if entry.title.text == name:
                return entry.id.text.rsplit('/', 1)[1]
        return None

    # gdata login operations
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
    
    # spreadsheet read operations
    def _read_order_data(self, ss_client, spreadsheet_name, order_key):
        vpp_order = dict()
        vpp_order['spreadsheet_name'] = spreadsheet_name
        vpp_order['codes'] = [ ]
        worksheet_feed = ss_client.GetWorksheetsFeed(order_key)
        worksheet_entry = worksheet_feed.entry[0]
        worksheet_key = worksheet_entry.id.text.rsplit('/', 1)[1]
        row_count = worksheet_entry.row_count.text
        # print "worksheet id: %s, %s rows" % (worksheet_key, row_count)
        cell_feed = ss_client.GetCellsFeed(order_key, worksheet_key)
        # print cell_feed.ToString()
        for i, entry in enumerate(cell_feed.entry):
            # Order Number: Row 2, Column 3 
            # app Name: Row 3, Column 3
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

    def _read_app_data(self, gd_client, spreadsheet_name, order_key):
        apps = dict()
        worksheet_feed = gd_client.GetWorksheetsFeed(order_key)
        worksheet_entry = worksheet_feed.entry[0]
        worksheet_key = worksheet_entry.id.text.rsplit('/', 1)[1]
        row_count = worksheet_entry.row_count.text
        # print "worksheet id: %s, %s rows" % (worksheet_key, row_count)
        query = gdata.spreadsheet.service.CellQuery()
        query['min-col'] = '1'
        query['max-col'] = '12'
        cell_feed = gd_client.GetCellsFeed(order_key, worksheet_key, query=query)
        name = None
        link = None
        price = None
        app_id = None
        groups = [ 'Group %d' % (i+1) for i in range(7) ]
        for i, entry in enumerate(cell_feed.entry):
            row = int(entry.cell.row)
            col = int(entry.cell.col)
            # print "R%dC%d: %s" % (row, col, entry.cell.text)
            if row == 1 and col >= 6 and col <= 12:
                # Header Row, group names
                groups[col-6] = entry.cell.text
            elif row >= 3:
                # app Rows, 3 to n
                # app Name: Column 1
                # App Store Link: Column 2
                # List Price: Column 3
                if col == 1:
                    name = entry.cell.text
                    link = None
                    price = None
                    app_id = None
                elif col == 2:
                    link = entry.cell.text
                elif col == 3:
                    price = entry.cell.text[1:] # strip dollar sign
                    if price == '' or price == '0':
                        price = '0.00'
                    m = re.search(r'\/id(\d+)\?', link) # extract id number
                    if m is not None:
                        app_id = m.group(1)
                        apps[app_id] = dict()
                        apps[app_id]['app_store_id'] = app_id
                        apps[app_id]['app_store_link'] = link
                        apps[app_id]['name'] = name
                        apps[app_id]['price'] = price
                        apps[app_id]['groups'] = [ ]
                elif app_id is not None and col >= 6 and col <= 12 and len(entry.cell.text) > 0:
                    apps[app_id]['groups'].append(groups[col-6])
        return apps
    
    # spreadsheet update operations
    def _find_vpp_code_in_spreadsheet(self, ss_client, spreadsheet_name, order_key, code):
        worksheet_feed = ss_client.GetWorksheetsFeed(order_key)
        worksheet_entry = worksheet_feed.entry[0]
        worksheet_key = worksheet_entry.id.text.rsplit('/', 1)[1]
        row_count = worksheet_entry.row_count.text
        # print "worksheet id: %s, %s rows" % (worksheet_key, row_count)
        query = gdata.spreadsheet.service.CellQuery()
        query['min-row'] = '11'        
        query['min-col'] = '1'        
        query['max_col'] = '1'        
        cell_feed = ss_client.GetCellsFeed(order_key, worksheet_key, query=query)
        for i, entry in enumerate(cell_feed.entry):
            # Rows 11 - 11+n:
            #  Redemption Link: Column 3
            #  Status: Column 4 (redeemed, reserved, etc)
            #  Device Name: Column 5
            #  Device Group: Column 6
            row = int(entry.cell.row)
            col = int(entry.cell.col)
            found_code = entry.cell.text
            if found_code == code:
                return (worksheet_key, row)
        return (None, None)
        
    def _update_vpp_cells_in_row(self, ss_client, spreadsheet_name, order_key, worksheet_key, row, status, user_email, device_name):
        print 'Updating row %d in %s: %s %s %s' % (row, spreadsheet_name, status, user_email, device_name)
        c4 = ss_client.UpdateCell(row=row, col=4, inputValue=status, 
            key=order_key, wksht_id=worksheet_key)
        if not isinstance(c4, gdata.spreadsheet.SpreadsheetsCell):
            print 'failed on col 4'
            return False
        c5 = ss_client.UpdateCell(row=row, col=5, inputValue=device_name, 
            key=order_key, wksht_id=worksheet_key)
        if not isinstance(c4, gdata.spreadsheet.SpreadsheetsCell):
            print 'failed on col 5'
            return False
        c6 = ss_client.UpdateCell(row=row, col=6, inputValue=user_email, 
            key=order_key, wksht_id=worksheet_key)
        if not isinstance(c4, gdata.spreadsheet.SpreadsheetsCell):
            print 'failed on col 6'
            return False
        print 'succeeded'
        return True

    def _next_pending_vpp_code(self, ss_client, app_id, user_email, device_name):
        db = self.db
        vpp_code = db((db.vpp_code.status=='Unused') & 
            (db.vpp_code.vpp_order==db.vpp_order.id) & 
            (db.vpp_order.app==app_id)).select(db.vpp_code.ALL, limitby=(0,1)).first()
        if vpp_code is not None:
            order_feed = ss_client.GetSpreadsheetsFeed()
            spreadsheet_name = vpp_code.vpp_order.spreadsheet_name
            order_key = self._find_spreadsheet(order_feed, spreadsheet_name)
            if order_key is not None:
                worksheet_key, row = self._find_vpp_code_in_spreadsheet(ss_client, spreadsheet_name, order_key, vpp_code.code)
                if row is not None:
                    success = self._update_vpp_cells_in_row(ss_client, spreadsheet_name, order_key, worksheet_key, row, 'Pending', user_email, device_name)
                    vpp_code.update_record(status='Pending')
                    return vpp_code
        return None
    
    # public interface    
    # utility methods
    def domain_user(self, user_email):
        if user_email is not None and user_email != '':
            if user_email.find('@') < 0:
                user_email += '@'
                user_email += self.settings.domain
            return user_email
        return None
        
    # spreadsheet read opearations
    def get_vpp_spreadsheets(self, coll_name=None):
        gd_client = self._docs_client()
        if coll_name is None:
            coll_name = self.settings.vpp_coll_name
        folder_feed = gd_client.GetDocList(uri='/feeds/default/private/full/-/folder?title=%s&title-exact=true&max-results=1' % (quote_plus(coll_name)))
        folder = folder_feed.entry[0]
        res_id = folder.resource_id.text
        order_feed = gd_client.GetDocList(uri='/feeds/default/private/full/%s/contents/-/spreadsheet?showfolders=false' % (res_id))
        order_titles = [ ]
        for order_entry in order_feed.entry:
            title = order_entry.title.text
            if title[0] != '_':
                order_titles.append(title)
        order_titles.sort(key=str.lower)
        return order_titles

    def read_orders(self, spreadsheet_names):
        results = dict()
        if len(spreadsheet_names) > 0:
            ss_client = self._ss_client()
            order_feed = ss_client.GetSpreadsheetsFeed()
            for spreadsheet_name in spreadsheet_names:
                order_key = self._find_spreadsheet(order_feed, spreadsheet_name)
                if order_key is None:
                    raise HTTP(500)
                    results[spreadsheet_name] = dict()
                else:
                    results[spreadsheet_name] = self._read_order_data(ss_client, spreadsheet_name, order_key)
        return results

    def read_apps(self, spreadsheet_name=None):
        results = dict()
        ss_client = self._ss_client()
        order_feed = ss_client.GetSpreadsheetsFeed()
        if spreadsheet_name is None:
            spreadsheet_name = self.settings.app_spreadsheet_name
        order_key = self._find_spreadsheet(order_feed, spreadsheet_name)
        if order_key is None:
            raise HTTP(500)
        else:
            results = self._read_app_data(ss_client, spreadsheet_name, order_key)
        return results    

    # database select operations
    def select_orders(self, update_list=False):
        db = self.db
        if update_list:
            spreadsheet_names = self.get_vpp_spreadsheets()
            for spreadsheet_name in spreadsheet_names:
                db.vpp_order.update_or_insert(spreadsheet_name=spreadsheet_name)
        return db().select(db.vpp_order.ALL, orderby=db.vpp_order.spreadsheet_name_nocase)

    def select_apps(self, group=None):
        db = self.db
        scope = None
        if group is not None:
            scope = db(db.app.groups.contains(group))
        else:
            scope = db()
        return scope.select(db.app.ALL, orderby=db.app.name_nocase)

    def select_groups(self):
        db = self.db
        return db().select(db.app_group.ALL, orderby=db.app_group.name)

    def select_devices(self):
        db = self.db
        return db().select(db.device.ALL, orderby=db.device.name)

    # database insert operations
    def populate_user_table(self):
        db = self.db
        file_name = self.settings.populate_folder + 'auth_user.csv'
        reader = csv.DictReader(open(file_name))
        for row in reader:
            email, email_error = db.auth_user.email.validate(row['email'])
            password, password_error = db.auth_user.password.validate(row['password'])
            if email_error is None and password_error is None:
                db.auth_user.insert(email=email, password=password,
                    first_name=row['first_name'],
                    last_name=row['last_name'])

    def populate_device_table(self):
        db = self.db
        file_name = self.settings.populate_folder + 'device.csv'
        reader = csv.DictReader(open(file_name))
        for row in reader:
            owner_id = None
            user_email = self.domain_user(row['user'])
            if user_email is not None:
                user = db(db.auth_user.email == user_email).select(limitby=(0,1)).first()
                if user is not None:
                    owner_id = user.id
            db.device.insert(name=row['name'],
                asset_number=row['asset_number'],
                serial_number=row['serial_number'],
                apple_device_id=row['apple_device_id'],
                location=row['location'],
                room=row['room'],
                owner=owner_id)
    
    def populate_app_table(self):             
        apps = self.read_apps()
        return self.update_apps(apps)

    def populate_order_table(self):
        spreadsheet_names = self.get_vpp_spreadsheets()
        vpp_orders = self.read_orders(spreadsheet_names)
        return self.update_orders(vpp_orders)

    # database update operations
    def update_orders(self, vpp_orders):
        db = self.db
        stats = dict(orders=0, redeemed=0, reserved=0, unused=0)
        for spreadsheet_name in vpp_orders.iterkeys():
            vpp_order = vpp_orders[spreadsheet_name]
            order_number = vpp_order['order_number']
            spreadsheet_name = vpp_order['spreadsheet_name']
            product_name = vpp_order['product_name']
            db.vpp_order.update_or_insert(db.vpp_order.spreadsheet_name==spreadsheet_name,
                order_number=order_number,
                spreadsheet_name=spreadsheet_name,
                product_name=product_name)
            db_order = db(db.vpp_order.spreadsheet_name==spreadsheet_name).select(limitby=(0,1)).first()
            stats['orders'] += 1
            for vpp_code in vpp_order['codes']:
                device = None
                owner = None
                device_name = vpp_code.get('device_name')
                user_email = self.domain_user(vpp_code.get('user_email'))
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
                    db.auth_user.update_or_insert(email=user_email)
                    owner = db(db.auth_user.email == user_email).select(limitby=(0,1)).first()
                    if device_name is None:
                        device_name = 'Unknown'
                    db.device.update_or_insert(name=device_name)
                    device = db(db.device.name == device_name).select(limitby=(0,1)).first()
                code = vpp_code['code']
                link = vpp_code['link']
                db.vpp_code.update_or_insert(db.vpp_code.code == code,
                    code=code, app_store_link=link, status=status,
                    vpp_order=db_order,
                    device=device,
                    owner=owner)
        return stats

    def update_apps(self, apps):
        db = self.db
        stats = dict(free=0, vpp=0)
        for app_store_id in apps.iterkeys():
            app = apps[app_store_id]
            name = app['name']
            link = app['app_store_link']
            price = app['price']
            group_ids = [ ]
            for group_name in app['groups']:
                db.app_group.update_or_insert(name=group_name)
                group = db(db.app_group.name == group_name).select(limitby=(0,1)).first()
                if group is not None:
                    group_ids.append(group.id)
            db.app.update_or_insert(db.app.app_store_id == app_store_id,
                name=name,
                name_nocase=name.upper(),
                app_store_id=app_store_id,
                app_store_link=link,
                groups=group_ids,
                price=price)
            if price == '0.00':
                stats['free'] += 1
            else:
                stats['vpp'] += 1
        return stats

    # email operations
    def queue_and_send_message(self, recipient, device, apps):
        ss_client = self._ss_client()
        body_lines = [ ]
        body_lines.append('Here are the links to your redemption codes and')
        body_lines.append('other download links for the apps you requested:')

        app_ids = [ ] 
        vpp_code_ids = [ ]
        for app in apps:
            app_ids.append(app.id)
            body_lines.append('')
            body_lines.append('%s:' % (app.name))
            vpp_code = self._next_pending_vpp_code(ss_client, app.id, recipient, device.name)
            if vpp_code is not None:
                if vpp_code:
                    vpp_code_ids.append(vpp_code.id)
                    body_lines.append('VPP: %s' % (vpp_code.app_store_link))
                else:
                    body_lines.append('$%s: %s' % (app.price, app.app_store_link))
        body_lines.append('')
        body_lines.append('--App Administrator')            

        subject = 'Download instructions for iPad apps'
        body = "\n".join(body_lines)

        db = self.db
        msg_id = db.invitation.insert(recipient=recipient,
            subject=subject,
            body=body,
            apps=app_ids,
            vpp_codes=vpp_code_ids)
        print 'inserted invitation %s' % (msg_id)

        if msg_id is not None and self.mailer is not None:
            success = self.mailer.send(to=[ recipient ], subject=subject, message=body)
            timestamp = datetime.now()
            status = 'Sent'
            if not success:
                status = 'Errors: %s' % (self.mailer.error)
            db.invitation(msg_id).update(last_sent_on=timestamp, last_status=status)
        return msg_id
