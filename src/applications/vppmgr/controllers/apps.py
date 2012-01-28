# -*- coding: utf-8 -*-
import re

def _find_app():
    app = db.app(request.args(0))
    if app is None:
         raise HTTP(404)
    return app

def index():
    app_rows = vpp_manager.select_apps()
    return dict(apps=app_rows)

def show():
    app = _find_app()
    return dict(form=SQLFORM(db.app, app, readonly=True))

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
        device = None
        device_id = request.post_vars['device']
        if device_id is None or device_id == '':
            errors.append('No device specified')
        else:
            device = db.device(device_id)
            if device is None:
                errors.append('Device not found')
        app_ids = [ ]
        for k in request.post_vars.iterkeys():
            m = re.match(r'app_(\d+)', k)
            if m is not None and request.post_vars[k] == '1':
                app_ids.append(int(m.group(1)))
        if len(app_ids) == 0:
            errors.append('No apps selected')
        if len(errors) > 0:
            response.flash = "\n".join(errors)
        else:
            apps = db(db.app.id.belongs(app_ids)).select()
            success = vpp_manager.queue_and_send_message(user_email, device, apps)
            if success:
                response.flash = "Message sent"
            else:
                response.flash = "Problem sending message"
    group_id = request.vars['group']
    group_name = None
    app_rows = vpp_manager.select_apps(group_id)
    group_rows = vpp_manager.select_groups()
    device_rows = vpp_manager.select_devices()
    if group_id is not None:
        group_names = [g.name for g in group_rows if g.id==int(group_id)]
        if len(group_names) > 0:
            group_name = group_names[0]
        else:
            group_id = None
    return dict(apps=app_rows, devices=device_rows, groups=group_rows, group=group_id, group_name=group_name)

def import_one():
    app = _find_app()
    updates = vpp_manager.update_apps([app])
    session.flash = "Updated %d free and %d vpp apps" % (updates['free'], updates['vpp'])
    redirect(URL('index'))

def import_all():
    updates = vpp_manager.populate_app_table()
    session.flash = "Updated %d free and %d vpp apps" % (updates['free'], updates['vpp'])
    redirect(URL('index'))
