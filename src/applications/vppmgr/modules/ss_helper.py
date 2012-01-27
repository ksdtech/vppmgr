# view helpers

def nearest_app_match(apps, spreadsheet_name):
    if len(apps) > 0:
        hi = 0
        product_name = None
        prev_name = None
        for i, app in enumerate(apps):
            product_name = app.name_nocase
            if prev_name is not None and spreadsheet_name >= prev_name and spreadsheet_name < product_name:
                return apps[i-1].id
            prev_name = product_name
            hi = i
        return apps[hi].id
    return None

def spreadsheet_import_link(spreadsheets, i):
    return '<a href="import_one/%d">Import %s</a>' % (spreadsheets[i].id, spreadsheets[i].spreadsheet_name)
    
def spreadsheet_app_select(spreadsheets, i, apps):
    select_id = 'order_%d' % (spreadsheets[i].id)
    selected_app = spreadsheets[i].app
    if selected_app is None:
        selected_app = nearest_app_match(apps, spreadsheets[i].spreadsheet_name_nocase)
    s = '<select name="%s" id="%s">' % (select_id, select_id)
    for app in apps:
        s += '<option value="%s"' % (app.id)
        if selected_app == app.id:
            s += ' selected="selected"'
        s += " />%s</option>" % (app.name)
    s += '</select>'
    return s