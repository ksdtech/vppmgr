# -*- coding: utf-8 -*-

def index():
    invites = db().select(db.invitation.ALL, orderby=~db.invitation.created_on)
    return dict(invites=invites)
