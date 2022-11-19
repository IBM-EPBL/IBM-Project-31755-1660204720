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
import timeago, datetime
from wtforms.fields import EmailField
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask_mail import Mail, Message
import plotly.graph_objects as go

#import smtplib
#from email.mime.multipart import MIMEMultipart
#from email.mime.text import MIMEText

import configparser
import ssl
ssl._create_default_https_context=ssl._create_unverified_context
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


app=Flask(__name__)

app.secret_key='a'

config=configparser.ConfigParser()
config.read("config.ini")

try:
    settings=config["SETTINGS"]
except:
    settings={}

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
            flash("The entered email address has already been taken.Please try using or creating another one.","info",)
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
       
class LoginForm(Form):
    username = StringField("Username", [validators.Length(min=4, max=100)])
    password = PasswordField(
        "Password",
        [
            validators.DataRequired(),
        ],
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if "logged_in" in session and session["logged_in"] == True:
        flash("You are already logged in", "info")
        return redirect(url_for("addTransactions"))
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        username = form.username.data
        password_input = form.password.data
        #database
        sql="SELECT * FROM user WHERE user_name=? or email=?"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,username)
        ibm_db.bind_param(stmt,2,username)
        ibm_db.execute(stmt)
        account=ibm_db.fetch_assoc(stmt)
        print(account)
        if account:
            userID = account["ID"]
            password = account["PASSWORD"]
            mailid=account["EMAIL"]
            role = account["ROLE"]
            if sha256_crypt.verify(password_input, password):
               session["logged_in"] = True
               session["username"] = username
               session["role"] = role
               session["userID"] = userID
               session["mailid"]=mailid
               flash("Logged in successfully!")
               return redirect(url_for("addTransactions"))
            else:
                error = "Invalid Password"
                return render_template("login.html", form=form, error=error)
        else:
            error = "Username not found"
            return render_template("login.html", form=form, error=error)

    return render_template("login.html", form=form)


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Please login", "info")
            return redirect(url_for("login"))
    return wrap
       
@app.route("/logout")
@is_logged_in
def logout():
    session.clear()
    flash("You are now logged out", "success")
    return redirect(url_for("login"))



@app.route("/addTransactions", methods=["GET", "POST"])
@is_logged_in
def addTransactions():
     if request.method == "POST" :
        amount = request.form["amount"]
        description = request.form["description"]
        category = request.form["category"]
        
        if(amount==""):
            flash("please enter the amount", "success")
            return redirect(url_for("addTransactions"))
        if(description==""):
            description="--"
        sql="SELECT SUM(amount) as AMT FROM transactions WHERE MONTH(date) = MONTH(CURRENT_TIMESTAMP) AND YEAR(date) = YEAR(CURRENT_TIMESTAMP) AND user_id = ?"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,session["userID"])
        ibm_db.execute(stmt)
        account=ibm_db.fetch_assoc(stmt)
        totalExpense = account["AMT"]

        sql="SELECT SUM(amount) as AMT FROM SALARY WHERE MONTH(date) = MONTH(CURRENT_TIMESTAMP) AND YEAR(date) = YEAR(CURRENT_TIMESTAMP) AND user_id = ?"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,session["userID"])
        ibm_db.execute(stmt)
        account=ibm_db.fetch_assoc(stmt)
        salary = account["AMT"]
        
        if salary==None and totalExpense==None:
            balance=0
        elif salary==None:
            balance=-totalExpense
        elif totalExpense==None:
            balance=salary
        else:
            balance=salary-totalExpense
        print(balance)
        print(amount)
        if (balance > int(amount)):    
           sql="INSERT INTO transactions(user_id, amount, description,category) VALUES(?,?,?,?)"
           stmt=ibm_db.prepare(conn,sql)
           ibm_db.bind_param(stmt,1,session["userID"])
           ibm_db.bind_param(stmt,2,amount)
           ibm_db.bind_param(stmt,3,description)
           ibm_db.bind_param(stmt,4,category)
           ibm_db.execute(stmt)
           flash("Transaction Successfully Recorded", "success")
           return redirect(url_for("addTransactions"))
        else:
            flash("Sorry you have not enough balance", "success")
            return redirect(url_for("addTransactions"))
     else:
        salary=0
        sql="SELECT SUM(amount) as AMT FROM transactions WHERE MONTH(date) = MONTH(CURRENT_TIMESTAMP) AND YEAR(date) = YEAR(CURRENT_TIMESTAMP) AND user_id = ?"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,session["userID"])
        ibm_db.execute(stmt)
        account=ibm_db.fetch_assoc(stmt)
        totalExpense = account["AMT"]

        sql="SELECT SUM(amount) as AMT FROM SALARY WHERE MONTH(date) = MONTH(CURRENT_TIMESTAMP) AND YEAR(date) = YEAR(CURRENT_TIMESTAMP) AND user_id = ?"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,session["userID"])
        ibm_db.execute(stmt)
        account=ibm_db.fetch_assoc(stmt)
        salary = account["AMT"]

        if salary==None and totalExpense==None:
            balance=0
        elif salary==None:
            balance=-totalExpense
        elif totalExpense==None:
            balance=salary
        else:
            balance=salary-totalExpense

        '''sql="SELECT * FROM user WHERE id = ?"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,session["userID"])
        ibm_db.execute(stmt)
        account=ibm_db.fetch_assoc(stmt)
        emailid=account["EMAIL"]
        print (emailid)'''
       
        if(balance<1000 and salary!=None):

            def sendMailUsingSendGrid(API,from_email,to_emails,subject,html_content):
                 message=Mail(from_email,to_emails,subject,html_content)
                 print(message)
                 try:
                   sg = SendGridAPIClient(API)
                   response = sg.send(message)
                   print(response.status_code)
                   print(response.body)
                   print(response.headers)
                 except Exception as e:
                   print(e.message)

            API=settings.get("APIKEY",None)
            from_email='personalexpensetrackerapp@gmail.com'
            to_email=session["mailid"]
            print(API)
            print(from_email)
            print(to_email)
            username=session['username']
            bal=str(balance)

            subject="Expense remainder"
            html_content="Hi "+username+", I hope you are well, "+ "you have reached minimum balance,"+"your remaining balance is " +bal +"."

            sendMailUsingSendGrid(API,from_email,to_email,subject,html_content)

            """text="hello "
            mail_content = '''your blance is reaches below 1000'''
#The mail addresses and password
            sender_address = 'personalexpensetrackerapp@gmail.com'
            sender_pass = 'yveyeuzwlqcqxcvw'
            receiver_address = emailid
#Setup the MIME
            message = MIMEMultipart()
            message['From'] = sender_address
            message['To'] = receiver_address
            message['Subject'] = 'Expense remainder.'   #The subject line
#The body and the attachments for the mail
            message.attach(MIMEText(mail_content, 'plain'))
#Create SMTP session for sending the mail
            ss = smtplib.SMTP('smtp.gmail.com', 587) #use gmail with port
            ss.starttls() #enable security
            ss.login(sender_address, sender_pass) #login with mail_id and password
            text = message.as_string()
            ss.sendmail(sender_address, receiver_address, text)
            ss.quit()
            print('Mail Sent')"""
          
         
        list=[]
        # get the month's transactions made by a particular user
        sql="SELECT * FROM transactions WHERE MONTH(date) = MONTH(CURRENT_TIMESTAMP) AND YEAR(date) = YEAR(CURRENT_TIMESTAMP) AND user_id = ? ORDER BY date DESC"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,session["userID"])
        ibm_db.execute(stmt)
        transactions=ibm_db.fetch_assoc(stmt)
        
        if transactions:
          while transactions!=False:
            list.append(transactions)
            transactions = ibm_db.fetch_assoc(stmt)

          for transaction in list:
                if datetime.datetime.now() - transaction["DATE"] < datetime.timedelta(days=0.5):
                    transaction["DATE"] = timeago.format(transaction["DATE"], datetime.datetime.now())
                else:
                    transaction["DATE"] = transaction["DATE"].strftime("%d %B, %Y")
          return render_template("addTransactions.html",totalExpenses=totalExpense,balances=balance,transactions=list)
        else:
            return render_template("addTransactions.html", result=transactions)
     return render_template("addTransactions.html")



@app.route("/addSalary", methods=["GET", "POST"])
@is_logged_in
def addSalary():
     if request.method == "POST":
        amount = request.form["amount"]
        description = request.form["description"]
        
        if(amount==""):
            flash("please enter the amount", "success")
            return redirect(url_for("addTransactions"))
        if(description==""):
            description="--"

        sql="INSERT INTO SALARY(user_id, amount, description) VALUES(?,?,?)"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,session["userID"])
        ibm_db.bind_param(stmt,2,amount)
        ibm_db.bind_param(stmt,3,description)
        ibm_db.execute(stmt)
        flash("Salary Successfully Recorded", "success")
        return redirect(url_for("addSalary"))

     else: 
        sql="SELECT SUM(amount) as AMT FROM SALARY WHERE MONTH(date) = MONTH(CURRENT_TIMESTAMP) AND YEAR(date) = YEAR(CURRENT_TIMESTAMP) AND user_id = ?"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,session["userID"])
        ibm_db.execute(stmt)
        account=ibm_db.fetch_assoc(stmt)
        totalExpense = account["AMT"]
         
        list=[]
       
        # get the month's transactions made by a particular user
        sql="SELECT * FROM SALARY WHERE MONTH(date) = MONTH(CURRENT_TIMESTAMP) AND YEAR(date) = YEAR(CURRENT_TIMESTAMP) AND user_id = ? ORDER BY date DESC"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,session["userID"])
        ibm_db.execute(stmt)
        transactions=ibm_db.fetch_assoc(stmt)
        
        if transactions:
          while transactions!=False:
            list.append(transactions)
            transactions = ibm_db.fetch_assoc(stmt)
 
          for transaction in list:
                if datetime.datetime.now() - transaction["DATE"] < datetime.timedelta(days=0.5):
                    transaction["DATE"] = timeago.format(transaction["DATE"], datetime.datetime.now())
                else:
                    transaction["DATE"] = transaction["DATE"].strftime("%d %B, %Y")
          return render_template("addSalary.html",totalExpenses=totalExpense,transactions=list)
        else:
            return render_template("addSalary.html", result=transactions)
     return render_template("addSalary.html")

@app.route("/transactionHistory", methods=["GET", "POST"])
@is_logged_in
def transactionHistory():
     if request.method == "POST":
        month = request.form["month"]
        year = request.form["year"]
      
        sql="SELECT SUM(amount) as AMT FROM transactions WHERE user_id = ?"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,session["userID"])
        ibm_db.execute(stmt)
        account=ibm_db.fetch_assoc(stmt)
        totalExpenses = account["AMT"]

        if month == "00":
            sql="SELECT SUM(amount) as AMT FROM transactions WHERE year(date) =?  AND user_id =?"
            stmt=ibm_db.prepare(conn,sql)
            ibm_db.bind_param(stmt,1,year)
            ibm_db.bind_param(stmt,2,session["userID"])
            ibm_db.execute(stmt)
            account=ibm_db.fetch_assoc(stmt)
            totalExpenses = account["AMT"]
 
            sql="SELECT * FROM transactions WHERE year(date) = ? AND user_id =? ORDER BY date DESC"
            stmt=ibm_db.prepare(conn,sql)
            ibm_db.bind_param(stmt,1,year)
            ibm_db.bind_param(stmt,2,session["userID"])
            ibm_db.execute(stmt)
            transactions =ibm_db.fetch_assoc(stmt)
        
        else:
            sql="SELECT SUM(amount) as AMT FROM transactions WHERE month(date) = ? AND year(date) = ? AND user_id = ?"
            stmt=ibm_db.prepare(conn,sql)
            ibm_db.bind_param(stmt,1,month)
            ibm_db.bind_param(stmt,2,year)
            ibm_db.bind_param(stmt,3,session["userID"])
            ibm_db.execute(stmt)
            account=ibm_db.fetch_assoc(stmt)
            totalExpenses = account["AMT"]

            sql="SELECT * FROM transactions WHERE month(date) = ? AND year(date) = ? AND user_id = ? ORDER BY date DESC"
            stmt=ibm_db.prepare(conn,sql)
            ibm_db.bind_param(stmt,1,month)
            ibm_db.bind_param(stmt,2,year)
            ibm_db.bind_param(stmt,3,session["userID"])
            ibm_db.execute(stmt)
            transactions =ibm_db.fetch_assoc(stmt)

        list=[] 
        if transactions:
            while transactions!=False:
              list.append(transactions)
              transactions = ibm_db.fetch_assoc(stmt)
            print (list);  
            for transaction in list:
                    transaction["DATE"] = transaction["DATE"].strftime("%d %B, %Y")
            return render_template("transactionHistory.html",totalExpenses=totalExpenses,transactions=list)
           
        
        else:
            monthName={"00":"true","01":"January","02":"February","03":"March","04":"April","05":"May","06":"June","07":"July","08":"August","09":"September","10":"October","11":"November","12":"December"}
            name=monthName[month]
        
            if name !="true" :
                msg = "No Transactions Found For "+name+","+ year
            else:
                msg = "No Transactions Found For "+year
            return render_template("transactionHistory.html", result=transactions,msg=msg)
     else:
        sql="SELECT SUM(amount) as AMT FROM transactions WHERE user_id = ?"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,session["userID"])
        ibm_db.execute(stmt)
            #fetchone
        account=ibm_db.fetch_assoc(stmt)
        totalExpenses = account["AMT"]

        list=[]

        # Get Latest Transactions made by a particular user
        sql="SELECT * FROM transactions WHERE user_id =? ORDER BY date DESC"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,session["userID"])
        ibm_db.execute(stmt)
        transactions = ibm_db.fetch_assoc(stmt)

        if transactions:
          while transactions!=False:
            list.append(transactions)
            transactions = ibm_db.fetch_assoc(stmt)

          print (list);  
          for transaction in list:
                    transaction["DATE"] = transaction["DATE"].strftime("%d %B, %Y")
          return render_template("transactionHistory.html",totalExpenses=totalExpenses,transactions=list)
           
        else:
            flash("No Transactions Found", "success")
            return redirect(url_for("addTransactions"))
        

@app.route("/salaryHistory", methods=["GET", "POST"])
@is_logged_in
def salaryHistory():
     if request.method == "POST":
        month = request.form["month"]
        year = request.form["year"]
        
        sql="SELECT SUM(amount) as AMT FROM SALARY WHERE user_id = ?"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,session["userID"])
        ibm_db.execute(stmt)
        #fetchone
        account=ibm_db.fetch_assoc(stmt)
        totalExpenses = account["AMT"]

        if month == "00":
            sql="SELECT SUM(amount) as AMT FROM SALARY WHERE year(date) =?  AND user_id =?"
            stmt=ibm_db.prepare(conn,sql)
            ibm_db.bind_param(stmt,1,year)
            ibm_db.bind_param(stmt,2,session["userID"])
            ibm_db.execute(stmt)
            #fetchone\
            account=ibm_db.fetch_assoc(stmt)
            totalExpenses = account["AMT"]
 
            sql="SELECT * FROM SALARY WHERE year(date) = ? AND user_id =? ORDER BY date DESC"
            stmt=ibm_db.prepare(conn,sql)
            ibm_db.bind_param(stmt,1,year)
            ibm_db.bind_param(stmt,2,session["userID"])
            ibm_db.execute(stmt)
            transactions =ibm_db.fetch_assoc(stmt)
        
        else:
            sql="SELECT SUM(amount) as AMT FROM SALARY WHERE month(date) = ? AND year(date) = ? AND user_id = ?"
            stmt=ibm_db.prepare(conn,sql)
            ibm_db.bind_param(stmt,1,month)
            ibm_db.bind_param(stmt,2,year)
            ibm_db.bind_param(stmt,3,session["userID"])
            ibm_db.execute(stmt)
            account=ibm_db.fetch_assoc(stmt)
            #fetchone
            totalExpenses = account["AMT"]

            sql="SELECT * FROM SALARY WHERE month(date) = ? AND year(date) = ? AND user_id = ? ORDER BY date DESC"
            stmt=ibm_db.prepare(conn,sql)
            ibm_db.bind_param(stmt,1,month)
            ibm_db.bind_param(stmt,2,year)
            ibm_db.bind_param(stmt,3,session["userID"])
            ibm_db.execute(stmt)
            transactions =ibm_db.fetch_assoc(stmt)

        list=[] 
        if transactions:
            while transactions!=False:
              list.append(transactions)
              transactions = ibm_db.fetch_assoc(stmt)
            print (list);  
            for transaction in list:
                    transaction["DATE"] = transaction["DATE"].strftime("%d %B, %Y")
            return render_template("salaryHistory.html",totalExpenses=totalExpenses,transactions=list)
           
        else:
            monthName={"00":"true","01":"jan","02":"feb"}
            name=monthName[month]
            print(name)
        
            if name !="true" :
                msg = "No Salary Found For "+name+","+ year
            else:
                msg = "No Salary Found For "+year
            return render_template("salaryHistory.html", result=transactions,msg=msg)
     else:
        sql="SELECT SUM(amount) as AMT FROM SALARY WHERE user_id = ?"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,session["userID"])
        ibm_db.execute(stmt)
            #fetchone
        account=ibm_db.fetch_assoc(stmt)
        totalExpenses = account["AMT"]

        list=[]

        # Get Latest Transactions made by a particular user
        sql="SELECT * FROM SALARY WHERE user_id =? ORDER BY date DESC"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,session["userID"])
        ibm_db.execute(stmt)
        transactions = ibm_db.fetch_assoc(stmt)

        
        if transactions:
          while transactions!=False:
            list.append(transactions)
            transactions = ibm_db.fetch_assoc(stmt)

          
          print (list);  
          for transaction in list:
                    transaction["DATE"] = transaction["DATE"].strftime("%d %B, %Y")
          return render_template("salaryHistory.html",totalExpenses=totalExpenses,transactions=list)
           
        else:
            flash("No Salary Found", "success")
            return redirect(url_for("addSalary"))
        
class TransactionForm(Form):
    amount = IntegerField("Amount", validators=[DataRequired()])
    description = StringField("Description", [validators.Length(min=1)])

@app.route("/editTransaction/<id>", methods=["GET", "POST"])
@is_logged_in
def editTransaction(id):
    sql="SELECT * FROM transactions WHERE ID = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,id)
    ibm_db.execute(stmt)
    transaction=ibm_db.fetch_assoc(stmt)
    
    # Get transaction by id
    # Get form
    form = TransactionForm(request.form)

    # Populate transaction form fields
    form.amount.data = transaction["AMOUNT"]
    form.description.data = transaction["DESCRIPTION"]

    if request.method == "POST" and form.validate():
        amount = request.form["amount"]
        description = request.form["description"]
    
        sql="UPDATE transactions SET AMOUNT=?, DESCRIPTION=? WHERE ID = ?",
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,amount)
        ibm_db.bind_param(stmt,2,description)
        ibm_db.bind_param(stmt,3,[id])
        ibm_db.execute(stmt)
   
        flash("Transaction Updated", "success")

        return redirect(url_for("transactionHistory"))

    return render_template("editTransaction.html", form=form)


# Delete transaction
@app.route("/deleteTransaction/<id>", methods=["POST"])
@is_logged_in
def deleteTransaction(id):

    sql="DELETE FROM transactions WHERE ID = ?" 
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,id)
    ibm_db.execute(stmt)

    flash("Transaction Deleted", "success")

    return redirect(url_for("transactionHistory"))

@app.route("/editSalary/<id>", methods=["GET", "POST"])
@is_logged_in
def editSalary(id):
    # Create cursor

    sql="SELECT * FROM SALARY WHERE ID = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,id)
    ibm_db.execute(stmt)
    transaction=ibm_db.fetch_assoc(stmt)
    

    # Get transaction by id
    # Get form
    form = TransactionForm(request.form)

    # Populate transaction form fields
    form.amount.data = transaction["AMOUNT"]
    form.description.data = transaction["DESCRIPTION"]

    if request.method == "POST" and form.validate():
        amount = request.form["amount"]
        description = request.form["description"]
        

        sql="UPDATE SALARY SET AMOUNT=?, DESCRIPTION=? WHERE ID = ?",
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,amount)
        ibm_db.bind_param(stmt,2,description)
        ibm_db.bind_param(stmt,3,[id])
        ibm_db.execute(stmt)
   

        flash("Salary Updated", "success")

        return redirect(url_for("SalaryHistory"))

    return render_template("editSalary.html", form=form)

@app.route("/deleteSalary/<id>", methods=["POST"])
@is_logged_in
def deleteSalary(id):

    sql="DELETE FROM SALARY WHERE ID = ?" 
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,id)
    ibm_db.execute(stmt)

    flash("Salary Deleted", "success")

    return redirect(url_for("salaryHistory"))

@app.route("/editCurrentMonthTransaction/<int:id>", methods=["GET", "POST"])
@is_logged_in
def editCurrentMonthTransaction(id):
    
   
    # Get form
    form = TransactionForm(request.form)


    if request.method == "POST" and form.validate():
        amount = request.form["amount"]
        description = request.form["description"]

        
        sql="UPDATE transactions SET (AMOUNT,DESCRIPTION) = (?,?) WHERE ID=? "
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,amount)
        ibm_db.bind_param(stmt,2,description)
        ibm_db.bind_param(stmt,3,id)
        ibm_db.execute(stmt)

        flash("Transaction Updated", "success")

        return redirect(url_for("addTransactions"))

    return render_template("editTransaction.html",form=form)

@app.route("/deleteCurrentMonthTransaction/<int:id>", methods=["POST"])
@is_logged_in
def deleteCurrentMonthTransaction(id):
    print(id)
    sql="DELETE FROM TRANSACTIONS WHERE ID = ?" 
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,id)
    ibm_db.execute(stmt)
    flash("Transaction Deleted", "success")
    return redirect(url_for("addTransactions"))

@app.route("/editCurrentMonthSalary/<int:id>", methods=["GET", "POST"])
@is_logged_in
def editCurrentMonthSalary(id):
    
   
    # Get form
    form = TransactionForm(request.form)


    if request.method == "POST" and form.validate():
        amount = request.form["amount"]
        description = request.form["description"]

        
        sql="UPDATE SALARY SET (AMOUNT,DESCRIPTION) = (?,?) WHERE ID=? "
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,amount)
        ibm_db.bind_param(stmt,2,description)
        ibm_db.bind_param(stmt,3,id)
        ibm_db.execute(stmt)

        flash("Transaction Updated", "success")

        return redirect(url_for("addSalary"))

    return render_template("editTransaction.html",form=form)

@app.route("/deleteCurrentMonthSalary/<int:id>", methods=["POST"])
@is_logged_in
def deleteCurrentMonthSalary(id):
    print(id)
    sql="DELETE FROM SALARY WHERE ID = ?" 
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,id)
    ibm_db.execute(stmt)
    flash("Salary Deleted", "success")
    return redirect(url_for("addSalary"))


# Category Wise Pie Chart For Current Year As Percentage #
@app.route("/category")
def createBarCharts():


    sql="SELECT SUM(amount) as amount,category FROM transactions WHERE YEAR(date) = YEAR(CURRENT_TIMESTAMP) AND user_id = ? GROUP BY category ORDER BY category"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)
    list=[];
    if transactions:
          while transactions!=False:
            list.append(transactions)
            transactions = ibm_db.fetch_assoc(stmt)   
          values = []
          labels = []  
          for transaction in list:
             values.append(transaction["AMOUNT"])
             labels.append(transaction["CATEGORY"])

          fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
          fig.update_traces(textinfo="label+value", hoverinfo="percent")
          fig.update_layout(title_text="Category Wise Pie Chart For Current Year")
          fig.show()
    
    return redirect(url_for("addTransactions"))



# Comparison Between Current and Previous Year #
@app.route("/yearly_bar")
def yearlyBar():
    sql="SELECT Sum(amount) as Amount FROM transactions WHERE MONTH(date) = 01  AND YEAR(date) = YEAR(CURRENT_TIMESTAMP)  AND user_id = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)

    if transactions:
        a1 = transactions["AMOUNT"]

    sql="SELECT Sum(amount) as Amount FROM transactions WHERE MONTH(date) = 01  AND YEAR(date) = year(CURRENT_TIMESTAMP)- 1 AND user_id = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)

    if transactions:
        a2 = transactions["AMOUNT"]

    sql="SELECT Sum(amount) as Amount FROM transactions WHERE MONTH(date) = 02  AND YEAR(date) = YEAR(CURRENT_TIMESTAMP)  AND user_id = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)

    if transactions:
        b1 = transactions["AMOUNT"]

    sql="SELECT Sum(amount) as Amount FROM transactions WHERE MONTH(date) = 02  AND YEAR(date) = year(CURRENT_TIMESTAMP)- 1  AND user_id = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)

    if transactions:
        b2 = transactions["AMOUNT"]

    sql="SELECT Sum(amount) as Amount FROM transactions WHERE MONTH(date) = 03  AND YEAR(date) = YEAR(CURRENT_TIMESTAMP)  AND user_id = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)

    if transactions:
        c1 = transactions["AMOUNT"]

    sql="SELECT Sum(amount) as Amount FROM transactions WHERE MONTH(date) = 03  AND YEAR(date) = year(CURRENT_TIMESTAMP)- 1  AND user_id = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)

    if transactions:
        c2 = transactions["AMOUNT"]
    
    sql="SELECT Sum(amount) as Amount FROM transactions WHERE MONTH(date) = 04  AND YEAR(date) = YEAR(CURRENT_TIMESTAMP)  AND user_id = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)

    if transactions:
        d1 = transactions["AMOUNT"]

    sql="SELECT Sum(amount) as Amount FROM transactions WHERE MONTH(date) = 04  AND YEAR(date) = year(CURRENT_TIMESTAMP)- 1  AND user_id = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)

    if transactions:
        d2 = transactions["AMOUNT"]

    sql="SELECT Sum(amount) as Amount FROM transactions WHERE MONTH(date) = 05  AND YEAR(date) = YEAR(CURRENT_TIMESTAMP)  AND user_id = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)

    if transactions:
        e1 = transactions["AMOUNT"]

    sql="SELECT Sum(amount) as Amount FROM transactions WHERE MONTH(date) = 05  AND YEAR(date) = year(CURRENT_TIMESTAMP)- 1  AND user_id = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)

    if transactions:
        e2 = transactions["AMOUNT"]

    sql="SELECT Sum(amount) as Amount FROM transactions WHERE MONTH(date) = 06  AND YEAR(date) = YEAR(CURRENT_TIMESTAMP)  AND user_id = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)

    if transactions:
        f1 = transactions["AMOUNT"]

    sql="SELECT Sum(amount) as Amount FROM transactions WHERE MONTH(date) = 06  AND YEAR(date) = year(CURRENT_TIMESTAMP)- 1  AND user_id = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)

    if transactions:
        f2 = transactions["AMOUNT"]

    sql="SELECT Sum(amount) as Amount FROM transactions WHERE MONTH(date) = 07  AND YEAR(date) = YEAR(CURRENT_TIMESTAMP)  AND user_id = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)

    if transactions:
        g1 = transactions["AMOUNT"]

    sql="SELECT Sum(amount) as Amount FROM transactions WHERE MONTH(date) = 07  AND YEAR(date) = year(CURRENT_TIMESTAMP)- 1  AND user_id = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)

    if transactions:
        g2 = transactions["AMOUNT"]

    sql="SELECT Sum(amount) as Amount FROM transactions WHERE MONTH(date) = 08  AND YEAR(date) = YEAR(CURRENT_TIMESTAMP)  AND user_id = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)

    if transactions:
        h1 = transactions["AMOUNT"]

    sql="SELECT Sum(amount) as Amount FROM transactions WHERE MONTH(date) = 08  AND YEAR(date) = year(CURRENT_TIMESTAMP)- 1  AND user_id = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)

    if transactions:
        h2 = transactions["AMOUNT"]

    sql="SELECT Sum(amount) as Amount FROM transactions WHERE MONTH(date) = 09  AND YEAR(date) = YEAR(CURRENT_TIMESTAMP)  AND user_id = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)

    if transactions:
        i1 = transactions["AMOUNT"]

    sql="SELECT Sum(amount) as Amount FROM transactions WHERE MONTH(date) = 09  AND YEAR(date) = year(CURRENT_TIMESTAMP)- 1  AND user_id = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)

    if transactions:
        i2 = transactions["AMOUNT"]

    sql="SELECT Sum(amount) as Amount FROM transactions WHERE MONTH(date) = 10  AND YEAR(date) = YEAR(CURRENT_TIMESTAMP)  AND user_id = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)

    if transactions:
        j1 = transactions["AMOUNT"]

    sql="SELECT Sum(amount) as Amount FROM transactions WHERE MONTH(date) = 10  AND YEAR(date) = year(CURRENT_TIMESTAMP)- 1  AND user_id = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)

    if transactions:
        j2 = transactions["AMOUNT"]
        
    sql="SELECT Sum(amount) as Amount FROM transactions WHERE MONTH(date) = 11  AND YEAR(date) = YEAR(CURRENT_TIMESTAMP)  AND user_id = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)

    if transactions:
        k1 = transactions["AMOUNT"]

    sql="SELECT Sum(amount) as Amount FROM transactions WHERE MONTH(date) = 11  AND YEAR(date) = year(CURRENT_TIMESTAMP)- 1  AND user_id = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)

    if transactions:
        k2 = transactions["AMOUNT"]

    sql="SELECT Sum(amount) as Amount FROM transactions WHERE MONTH(date) = 12  AND YEAR(date) = YEAR(CURRENT_TIMESTAMP)  AND user_id = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)

    if transactions:
        l1 = transactions["AMOUNT"]

    sql="SELECT Sum(amount) as Amount FROM transactions WHERE MONTH(date) = 12  AND YEAR(date) = year(CURRENT_TIMESTAMP)- 1  AND user_id = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)

    if transactions:
        l2 = transactions["AMOUNT"]


    sql="SELECT Sum(amount) as Amount FROM transactions WHERE  YEAR(date) = YEAR(CURRENT_TIMESTAMP)  AND user_id = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)

    if transactions:
       m1 = transactions["AMOUNT"]

    sql="SELECT Sum(amount) as Amount FROM transactions WHERE YEAR(date) = year(CURRENT_TIMESTAMP)- 1  AND user_id = ?"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)

    if transactions:
        m2 = transactions["AMOUNT"]
    

    year = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "June",
        "July",
        "Aug",
        "Sept",
        "Oct",
        "Nov",
        "Dec",
        "Total",
    ]
    fig = go.Figure(
        data=[
            go.Bar(
                name="Last Year",
                x=year,
                y=[a2, b2, c2, d2, e2, f2, g2, h2, i2, j2, k2, l2, m2],
            ),
            go.Bar(
                name="This Year",
                x=year,
                y=[a1, b1, c1, d1, e1, f1, g1, h1, i1, j1, k1, l1, m1],
            ),
        ]
    )
    fig.update_layout(
        barmode="group", title_text="Comparison Between This Year and Last Year"
    )
    fig.show()
    return redirect(url_for("addTransactions"))


# Current Year Month Wise #
@app.route("/daily_line")
def monthlyBar():

    sql="SELECT sum(amount) as amount, day(date) as date FROM transactions WHERE YEAR(date) = YEAR(CURRENT_TIMESTAMP) AND user_id = ? GROUP BY DATE ORDER BY DATE"
    stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(stmt,1,session["userID"])
    ibm_db.execute(stmt)  
    transactions=ibm_db.fetch_assoc(stmt)
    list=[];
    if transactions:
          while transactions!=False:
            list.append(transactions)
            transactions = ibm_db.fetch_assoc(stmt)   
          year = []
          value = []
          for transaction in list:
             year.append(transaction["DATE"])
             value.append(transaction["AMOUNT"])
          
          fig = go.Figure([go.Line(x=year, y=value)])
          fig.update_layout(title_text="Monthly Bar Chart For Current Year")
          fig.show()

    return redirect(url_for("addTransactions"))



if __name__=="__main__":
    app.run(debug=False,host='0.0.0.0',port=3002)