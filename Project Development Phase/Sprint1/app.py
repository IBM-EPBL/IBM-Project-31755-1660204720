from mailbox import Mailbox
import ibm_db
from flask import (
    Flask,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    session,
    logging,
    jsonify,
    Response,
)

from wtforms import (
    Form,
    StringField,
    PasswordField,
    TextAreaField,
    IntegerField,
    validators,
)
from wtforms.validators import DataRequired
from passlib.hash import sha256_crypt
from functools import wraps
from wtforms.fields import EmailField
from itsdangerous import Serializer

app=Flask(__name__)

app.secret_key='a'
try:
    conn=ibm_db.connect("DATABASE=bludb;HOSTNAME=1bbf73c5-d84a-4bb0-85b9-ab1a4348f4a4.c3n41cmd0nqnrk39u98g.databases.appdomain.cloud;PORT=32286;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=rcl83266;PWD=DKg9Id0Bx2ifwAHh","","")
    print("hi")
except:
    print("Unable to connect: ",ibm_db.conn_error())

@app.route("/")
def index():
    return render_template("index.html")

class RegistrationForm(Form):
    first_name = StringField("First Name", [validators.Length(min=1, max=100)])
    last_name = StringField("Last Name", [validators.Length(min=1, max=100)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email Address', [validators.Length(min=6, max=35)])
    password = PasswordField(
        "Password",
        [
            validators.DataRequired(),
            validators.EqualTo("confirm", message="Passwords do not match"),
        ],
    )
    confirm = PasswordField("Confirm Password")
       

@app.route('/register', methods=['GET', 'POST'])
def register():
    if "logged_in" in session and session["logged_in"] == True:
            flash("You are already logged in", "info")
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        first_name = form.first_name.data
        last_name = form.last_name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        #database
        sql="SELECT * FROM user WHERE email=?"
        prep_stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(prep_stmt,1,email)
        ibm_db.execute(prep_stmt)
        account=ibm_db.fetch_assoc(prep_stmt)
        if account:
            flash(
                "The entered email address has already been taken.Please try using or creating another one.",
                "info",
            )
            return redirect(url_for("register"))
        else:
               insert_sql="INSERT INTO user (FIRST_NAME,LAST_NAME,EMAIL,USER_NAME,PASSWORD) values(?,?,?,?,?)"
               prep_stmt=ibm_db.prepare(conn,insert_sql)
               ibm_db.bind_param(prep_stmt,1,first_name)
               ibm_db.bind_param(prep_stmt,2,last_name)
               ibm_db.bind_param(prep_stmt,3,email)
               ibm_db.bind_param(prep_stmt,4,username)
               ibm_db.bind_param(prep_stmt,5,password)
               ibm_db.execute(prep_stmt)
               flash(" Registration successfull. Log in to continue !")
               flash('Thanks for registering')
               return redirect(url_for('login'))
    return render_template('register.html', form=form)

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Please login", "info")
            return redirect(url_for("login"))

    return wrap
       
if __name__=="__main__":
    app.run(debug=True)
