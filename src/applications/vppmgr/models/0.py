from gluon.storage import Storage
settings = Storage()

# store usernames passewords, etc in separate module
from app_config import app_settings

settings.migrate = True
settings.title = 'VPP Code Manager'
settings.subtitle = 'powered by web2py'
settings.author = app_settings.author
settings.author_email = app_settings.email_sender
settings.keywords = ''
settings.description = 'Manages Apple VPP codes.  Import codes from Google Spreadsheet, manage deployment, email codes to users.'
settings.layout_theme = 'Default'
settings.database_uri = app_settings.database_uri
settings.security_key = 'ff0d4bcb-45d2-4275-ae44-8fc3ffc6425b'
settings.email_server = app_settings.email_server
settings.email_sender = app_settings.email_sender
settings.email_login = app_settings.email_login
settings.domain = app_settings.domain
settings.default_vpp_user = app_settings.default_vpp_user
settings.login_method = 'local'
settings.login_config = ''
settings.plugins = []
