def update_vpp_codes(db, settings, vpp_orders):
    stats = dict(orders=0, redeemed=0, reserved=0, unused=0)
    for ss_name in vpp_orders.iterkeys():
        vpp_order = vpp_orders[ss_name]
        order_number = vpp_order['order_number']
        spreadsheet_name = vpp_order['spreadsheet_name']
        product_name = vpp_order['product_name']
        order = db.vpp_order.update_or_insert(
            db.vpp_order.order_number == order_number and db.vpp_order.product_name == product_name,
            order_number=order_number,
            spreadsheet_name=spreadsheet_name,
            product_name=product_name)
        stats['orders'] += 1
        for vpp_code in vpp_order['codes']:
            device = None
            owner = None
            device_name = vpp_code.get('device_name')
            user_email = vpp_code.get('user_email')
            if user_email is not None:
                if user_email.find('@') < 0:
                    user_email += '@'
                    user_email += settings.domain
            status = vpp_code.get('status')
            if status is None:
                status = 'Unused'
                stats['unused'] += 1
            else:
                status = status.capitalize()
                if status == 'Redeemed':
                    stats['redeemed'] += 1
                else:
                    status = 'Reserved'
                    stats['reserved'] += 1         
                if user_email is None:
                    user_email = settings.default_vpp_user
                owner = db.auth_user.update_or_insert(db.auth_user.email == user_email,
                    email=user_email)
                if device_name is None:
                    device_name = 'Unknown'
                device = db.device.update_or_insert(db.device.name == device_name,
                    name=device_name)
            code = vpp_code['code']
            db.vpp_code.update_or_insert(db.vpp_code.code == code,
                code=code, status=status,
                vpp_order=order,
                device=device,
                owner=owner)
    return stats