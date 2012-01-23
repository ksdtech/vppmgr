import gdata.docs.data
import gdata.docs.client
import gdata.spreadsheet
import gdata.spreadsheet.service
import re
# from urllib import quote_plus

def find_spreadsheet(ss_feed, name):
    for entry in ss_feed.entry:
        # print entry.title.text
        if entry.title.text == name:
            return entry.id.text.rsplit('/', 1)[1]
    return None
  
def get_spreadsheets_in_collection(email, password, coll_name):
    gd_client = gdata.docs.client.DocsClient(source='vpp-app.kentfieldschools.org.1')
    gd_client.ClientLogin(email, password, gd_client.source)
    folder_feed = gd_client.GetDocList(uri='/feeds/default/private/full/-/folder?title=%s&title-exact=true&max-results=1' % (quote_plus(coll_name)))
    folder = folder_feed.entry[0]
    res_id = folder.resource_id.text
    ss_feed = gd_client.GetDocList(uri='/feeds/default/private/full/%s/contents/-/spreadsheet?showfolders=false' % (res_id))
    ss_titles = [ ]
    for ss_entry in ss_feed.entry:
        title = ss_entry.title.text
        if title[0] != '_':
            ss_titles.append(title)
    ss_titles.sort()
    return ss_titles

def ss_service_client(email, password):
    ss_client = gdata.spreadsheet.service.SpreadsheetsService()
    ss_client.email = email
    ss_client.password = password
    ss_client.source = 'vpp-app.kentfieldschools.org.1'
    ss_client.ProgrammaticLogin()
    return ss_client

def read_vpp_data(gd_client, ss_name, ss_key):
    vpp_order = dict()
    vpp_order['spreadsheet_name'] = ss_name
    vpp_order['codes'] = [ ]
    ss_ws_feed = gd_client.GetWorksheetsFeed(ss_key)
    ws_entry = ss_ws_feed.entry[0]
    ws_key = ws_entry.id.text.rsplit('/', 1)[1]
    row_count = ws_entry.row_count.text
    # print "worksheet id: %s, %s rows" % (ws_key, row_count)
    cell_feed = gd_client.GetCellsFeed(ss_key, ws_key)
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

def read_product_data(gd_client, ss_name, ss_key):
    products = dict()
    ss_ws_feed = gd_client.GetWorksheetsFeed(ss_key)
    ws_entry = ss_ws_feed.entry[0]
    ws_key = ws_entry.id.text.rsplit('/', 1)[1]
    row_count = ws_entry.row_count.text
    # print "worksheet id: %s, %s rows" % (ws_key, row_count)
    query = gdata.spreadsheet.service.CellQuery()
    query['min-col'] = '1'
    query['max-col'] = '3'
    query['min-row'] = '3'
    cell_feed = gd_client.GetCellsFeed(ss_key, ws_key, query=query)
    name = None
    link = None
    price = None
    for i, entry in enumerate(cell_feed.entry):
        # Product Name: Column 1
        # App Store Link: Column 2
        # List Price: Column 3
        col = int(entry.cell.col)
        if col == 1:
            name = entry.cell.text
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
            name = None
            link = None
            price = None
    return products

def read_vpp_orders(email, password, ss_names):
    results = dict()
    if len(ss_names) > 0:
        ss_client = ss_service_client(email, password)
        ss_feed = ss_client.GetSpreadsheetsFeed()
        for ss_name in ss_names:
            ss_key = find_spreadsheet(ss_feed, ss_name)
            if ss_key is None:
                raise HTTP(500)
                results[ss_name] = dict()
            else:
                results[ss_name] = read_vpp_data(ss_client, ss_name, ss_key)
    return results

def read_products(email, password, ss_name):
    results = dict()
    ss_client = ss_service_client(email, password)
    ss_feed = ss_client.GetSpreadsheetsFeed()
    ss_key = find_spreadsheet(ss_feed, ss_name)
    if ss_key is None:
        raise HTTP(500)
    else:
        results = read_product_data(ss_client, ss_name, ss_key)
    return results