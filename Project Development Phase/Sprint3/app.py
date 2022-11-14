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


print(balance)

if __name__=="__main__":
    app.run(debug=True)
