response.title = settings.title
response.subtitle = settings.subtitle
response.meta.author = '%(author)s <%(author_email)s>' % settings
response.meta.keywords = settings.keywords
response.meta.description = settings.description
response.menu = [
    (T('Home'),         URL('default','index')==URL(),      URL('default','index'), []),
    (T('Spreadsheets'), URL('spreadsheets','index')==URL(), URL('spreadsheets','index'), [
        (T('List'),        URL('spreadsheets','index')==URL(),       URL('spreadsheets','index'), []),
        (T('Import All'),  URL('spreadsheets','import_all')==URL(),  URL('spreadsheets','import_all'), []),
        (T('Assign Apps'), URL('spreadsheets','assign_apps')==URL(), URL('spreadsheets','assign_apps'), []),
        (T('Clear Apps'),  URL('spreadsheets','clear_apps')==URL(),  URL('spreadsheets','clear_apps'), [])
    ]),
]