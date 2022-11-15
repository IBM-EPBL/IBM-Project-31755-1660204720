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
from itsdangerous import Serializer
from flask_mail import Mail, Message
import plotly.graph_objects as go


app=Flask(__name__)

balance=0;

app.secret_key='a'
try:
    conn=ibm_db.connect("DATABASE=bludb;HOSTNAME=1bbf73c5-d84a-4bb0-85b9-ab1a4348f4a4.c3n41cmd0nqnrk39u98g.databases.appdomain.cloud;PORT=32286;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=rcl83266;PWD=DKg9Id0Bx2ifwAHh","","")
    print("hi")
except:
    print("Unable to connect: ",ibm_db.conn_error())

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    if "logged_in" in session and session["logged_in"] == True:
        flash("You are already logged in", "info")
        return redirect(url_for("index"))
    s = Serializer(app.config["SECRET_KEY"])
    try:
        user_id = s.loads(token)["user_id"]
    except:
        flash("That is an invalid or expired token", "warning")
        return redirect(url_for("reset_request"))
    
    sql="SELECT id FROM user WHERE id=?"
    prep_stmt=ibm_db.prepare(conn,sql)
    ibm_db.bind_param(prep_stmt,1,user_id)
    ibm_db.execute(prep_stmt)
    account=ibm_db.fetch_assoc(prep_stmt)
    user_id = account["ID"]
    form = ResetPasswordForm(request.form)
    if request.method == "POST" and form.validate():
        password = sha256_crypt.encrypt(str(form.password.data))
        sql="UPDATE user SET password =? WHERE id = ?"
        ibm_db.bind_param(prep_stmt,1,password)
        ibm_db.bind_param(prep_stmt,2,user_id)
        ibm_db.execute(prep_stmt)
        flash("Your password has been updated! You are now able to log in", "success")
        return redirect(url_for("login"))
    return render_template("reset_token.html", title="Reset Password", form=form)

@app.route("/addTransactions", methods=["GET", "POST"])
@is_logged_in
def addTransactions():
     if request.method == "POST":
        amount = request.form["amount"]
        description = request.form["description"]
        category = request.form["category"]

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
        
        sql="SELECT SUM(amount) as AMT FROM transactions WHERE MONTH(date) = MONTH(CURRENT_TIMESTAMP) AND YEAR(date) = YEAR(CURRENT_TIMESTAMP) AND user_id = ?"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,session["userID"])
        ibm_db.execute(stmt)
        #fetchone
        account=ibm_db.fetch_assoc(stmt)
        totalExpense = account["AMT"]

        
        sql="SELECT SUM(amount) as AMT FROM SALARY WHERE MONTH(date) = MONTH(CURRENT_TIMESTAMP) AND YEAR(date) = YEAR(CURRENT_TIMESTAMP) AND user_id = ?"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,session["userID"])
        ibm_db.execute(stmt)
        #fetchone
        account=ibm_db.fetch_assoc(stmt)
        salary = account["AMT"]

        balance=salary-totalExpense
         
        list=[]
       
        # get the month's transactions made by a particular user
        sql="SELECT * FROM transactions WHERE MONTH(date) = MONTH(CURRENT_TIMESTAMP) AND YEAR(date) = YEAR(CURRENT_TIMESTAMP) AND user_id = ? ORDER BY date DESC"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,session["userID"])
        ibm_db.execute(stmt)
        transactions=ibm_db.fetch_assoc(stmt)
        
        if transactions:
          while transactions!=False:
           # inlist.append(transactions["DATE"])
            #inlist.append(transactions["AMOUNT"])
            #inlist.append(transactions["USER_ID"])
            #inlist.append(transactions["ID"])
            #inlist.append(transactions["CATEGORY"])
            #inlist.append(transactions["DESCRIPTION"])
            #list.append(inlist)
            list.append(transactions)
            transactions = ibm_db.fetch_assoc(stmt)

          
          print (list);  
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

          
          print (list);  
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

        print(month)
        print(year)
      
        
        sql="SELECT SUM(amount) as AMT FROM transactions WHERE user_id = ?"
        stmt=ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,session["userID"])
        ibm_db.execute(stmt)
        #fetchone
        account=ibm_db.fetch_assoc(stmt)
        totalExpenses = account["AMT"]


        if month == "00":

            sql="SELECT SUM(amount) as AMT FROM transactions WHERE year(date) =?  AND user_id =?"
            stmt=ibm_db.prepare(conn,sql)
            ibm_db.bind_param(stmt,1,year)
            ibm_db.bind_param(stmt,2,session["userID"])
            ibm_db.execute(stmt)
            #fetchone\
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
            #fetchone
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
            #inlist.append(transactions["DATE"])
            #inlist.append(transactions["AMOUNT"])
            #inlist.append(transactions["USER_ID"])
            #inlist.append(transactions["ID"])
            #inlist.append(transactions["CATEGORY"])
            #inlist.append(transactions["DESCRIPTION"])
            #list.append(inlist)
              list.append(transactions)
              transactions = ibm_db.fetch_assoc(stmt)
            print (list);  
            for transaction in list:
                    transaction["DATE"] = transaction["DATE"].strftime("%d %B, %Y")
            return render_template("transactionHistory.html",totalExpenses=totalExpenses,transactions=list)
           
        
        else:
            monthName={"00":"true","01":"January","02":"February","03":"March","04":"April","05":"May","06":"June","07":"July","08":"August","09":"September","10":"October","11":"November","12":"December"}
            name=monthName[month]
            print(name)
        
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
           # inlist.append(transactions["DATE"])
            #inlist.append(transactions["AMOUNT"])
            #inlist.append(transactions["USER_ID"])
            #inlist.append(transactions["ID"])
            #inlist.append(transactions["CATEGORY"])
            #inlist.append(transactions["DESCRIPTION"])
            #list.append(inlist)
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

        print(month)
        print(year)
      
        
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
            #inlist.append(transactions["DATE"])
            #inlist.append(transactions["AMOUNT"])
            #inlist.append(transactions["USER_ID"])
            #inlist.append(transactions["ID"])
            #inlist.append(transactions["CATEGORY"])
            #inlist.append(transactions["DESCRIPTION"])
            #list.append(inlist)
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
           # inlist.append(transactions["DATE"])
            #inlist.append(transactions["AMOUNT"])
            #inlist.append(transactions["USER_ID"])
            #inlist.append(transactions["ID"])
            #inlist.append(transactions["CATEGORY"])
            #inlist.append(transactions["DESCRIPTION"])
            #list.append(inlist)
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
    # Create cursor

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
