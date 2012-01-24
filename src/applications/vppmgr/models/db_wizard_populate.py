# from gluon.contrib.populate import populate
import csv

if db(db.auth_user).isempty():
    # populate(db.auth_user,10)
    user_reader = csv.DictReader(open(app_settings.user_file))
    for row in user_reader:
        email, email_error = db.auth_user.email.validate(row['email'])
        password, password_error = db.auth_user.password.validate(row['password'])
        if email_error is None and password_error is None:
            db.auth_user.insert(email=email, password=password,
                first_name=row['first_name'],
                last_name=row['last_name'])
