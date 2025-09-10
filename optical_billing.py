from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3, os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

app = Flask(__name__)
app.secret_key = "supersecretkey"

DB_FILE = "billing.db"

# Initialize DB
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS customers
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         name TEXT, contact TEXT,
         right_sph TEXT, right_cyl TEXT, right_axis TEXT,
         left_sph TEXT, left_cyl TEXT, left_axis TEXT,
         add_power TEXT, glasses_type TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users
        (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Ensure invoices folder exists
if not os.path.exists("invoices"):
    os.makedirs("invoices")

# Default login (username: admin, password: admin)
def add_default_user():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", ("admin",))
    if not c.fetchone():
        c.execute("INSERT INTO users (username,password) VALUES (?,?)", ("admin", "admin"))
    conn.commit()
    conn.close()

add_default_user()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u, p = request.form["username"], request.form["password"]
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
        if c.fetchone():
            session["user"] = u
            return redirect("/dashboard")
        return "❌ Invalid login"
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html")

@app.route("/add_customer", methods=["GET","POST"])
def add_customer():
    if "user" not in session:
        return redirect("/")
    glasses_types = ["Blue Cut", "Blue Light", "Premium", "Daynight", "HMC", "Polycarbonate"]
    if request.method == "POST":
        data = (
            request.form["name"], request.form["contact"],
            request.form["right_sph"], request.form["right_cyl"], request.form["right_axis"],
            request.form["left_sph"], request.form["left_cyl"], request.form["left_axis"],
            request.form["add_power"], request.form["glasses_type"]
        )
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO customers (name, contact, right_sph, right_cyl, right_axis, left_sph, left_cyl, left_axis, add_power, glasses_type) VALUES (?,?,?,?,?,?,?,?,?,?)", data)
        conn.commit()
        conn.close()
        return redirect("/customers")
    return render_template("add_customer.html", glasses_types=glasses_types)

@app.route("/customers")
def customers():
    if "user" not in session:
        return redirect("/")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM customers")
    customers = c.fetchall()
    conn.close()
    return render_template("customers.html", customers=customers)

@app.route("/invoice/<int:cid>")
def invoice(cid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM customers WHERE id=?", (cid,))
    customer = c.fetchone()
    conn.close()

    if not customer:
        return "Customer not found!"

    file_path = f"invoices/invoice_{cid}.pdf"
    c_pdf = canvas.Canvas(file_path, pagesize=letter)
    c_pdf.drawString(50, 750, "getchasma.com - Optical Shop Invoice")
    c_pdf.drawString(50, 730, f"Name: {customer[1]}")
    c_pdf.drawString(50, 715, f"Contact: {customer[2]}")
    c_pdf.drawString(50, 690, f"Right Eye: SPH {customer[3]} CYL {customer[4]} Axis {customer[5]}")
    c_pdf.drawString(50, 675, f"Left Eye: SPH {customer[6]} CYL {customer[7]} Axis {customer[8]}")
    c_pdf.drawString(50, 660, f"ADD: {customer[9]}")
    c_pdf.drawString(50, 645, f"Glasses Type: {customer[10]}")
    c_pdf.save()

    return send_file(file_path, as_attachment=True)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
