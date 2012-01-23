# -*- coding: utf-8 -*-
### required - do no delete
def user(): return dict(form=auth())
def download(): return response.download(request,db)
def call(): return service()
### end requires

def index():
    return dict()

def error():
    return dict()
    
def display_form():
    record = db.vpp_order(request.args(0)) or redirect(URL('index'))
    form = SQLFORM(db.vpp_order, record)
    if form.process().accepted:
        response.flash = 'form accepted'
    elif form.errors:
        response.flash = 'form has errors'
    return dict(form=form)
