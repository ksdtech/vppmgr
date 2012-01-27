# view helpers
import difflib

def nearest_app_match(apps, spreadsheet_name):
    app_id = None
    if len(apps) > 0:
        name = spreadsheet_name
        l = len(spreadsheet_name)
        if l > 20:
            # truncate at '- ' or '(')
            t = spreadsheet_name.find('- ')
            x = spreadsheet_name.find('(')
            if x > 0 and (t < 0 or x < t):
                t = x
            if t > 0:
                l = t
                name = spreadsheet_name[0:l]
        app_names = [app.name_nocase[0:l] for app in apps]
        app_name_matches = difflib.get_close_matches(name, app_names, 1)
        if len(app_name_matches) > 0:
            app_name = app_name_matches[0]
            app_id = [app.id for app in apps if app.name_nocase[0:l]==app_name][0]
        else:
            print "no close match for %s (%s)" % (spreadsheet_name, name)
    return app_id

def spreadsheet_import_link(spreadsheets, i):
    return '<a href="import_one/%d">Import %s</a>' % (spreadsheets[i].id, spreadsheets[i].spreadsheet_name)
    
def spreadsheet_app_select(spreadsheets, i, apps):
    select_id = 'order_%d' % (spreadsheets[i].id)
    selected_app = spreadsheets[i].app
    if selected_app is None:
        selected_app = nearest_app_match(apps, spreadsheets[i].spreadsheet_name_nocase)
    s = '<select name="%s" id="%s">' % (select_id, select_id)
    s += '<option value="">--Select the matching app</option>'
    for app in apps:
        s += '<option value="%s"' % (app.id)
        if selected_app == app.id:
            s += ' selected="selected"'
        s += " />%s</option>" % (app.name)
    s += '</select>'
    return s