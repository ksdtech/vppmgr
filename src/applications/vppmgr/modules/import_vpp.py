import gdata.docs.data
import gdata.docs.client
import gdata.spreadsheet
import gdata.spreadsheet.service

def find_spreadsheet(ss_feed, name):
    for entry in ss_feed.entry:
        if entry.title.text == name:
            return entry.id.text.rsplit('/', 1)[1]
    return None
  
def get_spreadsheets_in_collection(email, password, coll_name):
    gd_client = gdata.docs.client.DocsClient(source='vpp-app.kentfieldschools.org.1')
    gd_client.ClientLogin(email, password, gd_client.source)
    folder_feed = gd_client.GetDocList(uri='/feeds/default/private/full/-/folder?title=%s&title-exact=true&max-results=1' % (coll_name))
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

def import_google_vpp_spreadsheets(email, password, ss_names):
    results = dict()
    if len(ss_names) > 0:
        ss_client = gdata.spreadsheet.service.SpreadsheetsService()
        ss_client.email = email
        ss_client.password = password
        ss_client.source = 'vpp-app.kentfieldschools.org.1'
        ss_client.ProgrammaticLogin()
        ss_feed = ss_client.GetSpreadsheetsFeed()
        for ss_name in ss_names:
            ss_key = find_spreadsheet(ss_feed, ss_name)
            if ss_key is None:
                raise HTTP(500)
                results[ss_name] = dict()
            else:
                results[ss_name] = read_vpp_data(ss_client, ss_name, ss_key)
    return results
