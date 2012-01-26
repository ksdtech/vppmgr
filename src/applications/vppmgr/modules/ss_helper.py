# view helpers

def nearest_app_match(apps, ss_name):
    if len(apps) > 0:
        hi = 0
        app_name = None
        prev_name = None
        for i, product in enumerate(apps):
            app_name = product.name_nocase
            if prev_name is not None and ss_name >= prev_name and ss_name < app_name:
                return apps[i-1].id
            prev_name = app_name
            hi = i
        return apps[hi].id
    return None

def spreadsheet_import_link(spreadsheets, i):
    return '<a href="import_one/%d">Import %s</a>' % (spreadsheets[i].id, spreadsheets[i].spreadsheet_name)
    
def spreadsheet_app_select(spreadsheets, i, apps):
    select_id = 'ss_%d' % (spreadsheets[i].id)
    selected_app = spreadsheets[i].product
    if selected_app is None:
        selected_app = nearest_app_match(apps, spreadsheets[i].spreadsheet_name_nocase)
    s = '<select name="%s" id="%s">' % (select_id, select_id)
    for product in apps:
        s += '<option value="%s"' % (product.id)
        if selected_app == product.id:
            s += ' selected="selected"'
        s += " />%s</option>" % (product.name)
    s += '</select>'
    return s