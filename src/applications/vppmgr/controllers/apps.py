# -*- coding: utf-8 -*-
import re

def _find_app():
    app = db.app(request.args(0))
    if app is None:
         raise HTTP(404)
    return app
    
def _filtered_by_group():
    group_id = request.vars['group']
    group_name = None
    app_rows = vpp_manager.select_apps(group_id)
    group_rows = vpp_manager.select_groups()
    if group_id is not None:
        group_names = [g.name for g in group_rows if g.id==int(group_id)]
        if len(group_names) > 0:
            group_name = group_names[0]
        else:
            group_id = None
    return (app_rows, group_rows, group_id, group_name)
    
def index():
    app_rows, group_rows, group_id, group_name = _filtered_by_group()
    return dict(apps=app_rows, groups=group_rows, group=group_id, group_name=group_name)

def show():
    app = _find_app()
    return dict(app=app, form=SQLFORM(db.app, app, readonly=True))

def provision():
    if request.env.request_method == 'POST': # postback
        errors = []
        user_email = vpp_manager.domain_user(request.post_vars['user_email'])
        if user_email is None:
            errors.append('No user specified')
        else:
            user_count = db(db.auth_user.email == user_email).count()
            if user_count < 1:
                errors.append('No such user: %s' % (user_email))
        devices = None
        device_ids = request.post_vars['devices']
        # multiple select returns single string if only one selected!
        if (isinstance(device_ids, str)):
            device_ids = [ device_ids ]
        if len(device_ids) == 0:
            errors.append('No devices selected')
        else:
            devices = db(db.device.id.belongs(device_ids)).select(db.device.ALL)
            if len(devices) == 0:
                errors.append('No devices found')
        apps = None
        app_ids = request.post_vars['apps']
        # multiple select returns single string if only one selected!
        if (isinstance(app_ids, str)):
            app_ids = [ app_ids ]
        if len(app_ids) == 0:
            errors.append('No apps selected')
        else:
            apps = db(db.app.id.belongs(app_ids)).select()
            if len(apps) == 0:
                errors.append('No apps found')
        if len(errors) == 0:
            success = vpp_manager.queue_and_send_message(user_email, devices, apps)
            if success:
                response.flash = "Message sent"
            else:
                response.flash = "Problem sending message"
        else:
            response.flash = "\n".join(errors)
    app_rows, group_rows, group_id, group_name = _filtered_by_group()
    user_rows = db().select(db.auth_user.ALL, orderby=db.auth_user.email)
    device_rows = vpp_manager.select_devices()
    return dict(apps=app_rows, groups=group_rows, group=group_id, group_name=group_name, users=user_rows, devices=device_rows)

def import_one():
    app = _find_app()
    updates = vpp_manager.update_apps([app])
    session.flash = "Updated %d free and %d vpp apps" % (updates['free'], updates['vpp'])
    redirect(URL('index'))

def import_all():
    updates = vpp_manager.populate_app_table()
    session.flash = "Updated %d free and %d vpp apps" % (updates['free'], updates['vpp'])
    redirect(URL('index'))
