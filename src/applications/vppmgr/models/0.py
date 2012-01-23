from gluon.storage import Storage
settings = Storage()

settings.migrate = True
settings.title = 'VPP Code Manager'
settings.subtitle = 'powered by web2py'
settings.author = 'you'
settings.author_email = 'you@example.com'
settings.keywords = ''
settings.description = 'Manages Apple VPP codes.  Import codes from Google Spreadsheet, manage deployment, email codes to users.'
settings.layout_theme = 'Default'
settings.database_uri = 'sqlite://vpp.sqlite'
settings.security_key = '32f2a292-1383-4ad7-8d4b-76ce314fbddb'
settings.email_server = 'localhost'
settings.email_sender = 'you@example.com'
settings.email_login = ''
settings.login_method = 'local'
settings.login_config = ''
settings.plugins = []
