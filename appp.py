from flask import Flask, render_template, request, redirect, session, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import join
import sqlite3
from datetime import datetime


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)
app.secret_key = "abc123"


# ===================== MODELS =======================
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    clock_in = db.Column(db.String)
    clock_out = db.Column(db.String)   

class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), default="student")


# ===================== HOME =======================

@app.route('/')
def index():
    return redirect("/registerpage")

# ======================admin========================
@app.route("/admin")
def admin_page():
    records = db.session.query(
        Attendance.id,
        User.username,
        Attendance.clock_in,
        Attendance.clock_out
    ).join(User, Attendance.user_id == User.user_id).all()

    return render_template("admin_home.html", data=records)


# ======================student=====================
@app.route("/student")
def student_page():
    return render_template("student_home.html")


# ===================== LOGIN =======================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        selected_role = request.form.get("role")

        user = User.query.filter_by(username=username).first()

        if user is None:
            error_message = "User not found!"
            return render_template("login.html", error=error_message)
        if user.password != password:
            error_message = "Wrong password!"
            return render_template("login.html", error=error_message)
        if user.role != selected_role:
             error_message = f"Role mismatch! This user is '{user.role}'."
             return render_template("login.html", error=error_message)
    

        session["user_id"] = user.user_id
        session["role"] = user.role
        session["username"] = user.username

        if user.role == "admin":
            return redirect("/admin")
        
        return redirect("/homepage")

    return render_template("login.html")



# ===================== SIGNUP =======================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username=request.form.get("username")
        email=request.form.get("email")
        password=request.form.get("password")

        existing = User.query.filter_by(username=username).first()
        if existing:
            return "username already exist!"
        new_user=User(username=username, email=email, password=password, role="student")

        db.session.add(new_user)
        db.session.commit()

        return redirect("/login")

    # return render_template("Signup.html")


# ===================== HOMEPAGE =======================
@app.route("/homepage")
def homepage():
    if "role" not in session:
        return redirect("/login")
    
    if session["role"] == "admin":
        all_data = Attendance.query.all()
        return render_template("admin_home.html", data=all_data)

    user_id = session["user_id"]

    student_records = db.session.query(
        User.username,
        Attendance.clock_in,
        Attendance.clock_out
    ).join(User, Attendance.user_id == User.user_id)\
     .filter(Attendance.user_id == user_id).all()
    
    return render_template(
        "student_home.html",
        username=session["username"],
        data=student_records
    )


# ===================== registerpage =======================
@app.route('/registerpage')
def page2():
    return render_template("registerpage.html")

# ======================delete========================
@app.route("/delete/<int:id>", methods=["POST"])
def delete_record(id):
    record = Attendance.query.get(id)

    if record:
        db.session.delete(record)
        db.session.commit()

    return redirect("/admin")

# ===================== CLOCK IN =======================
@app.route("/clockin", methods=["POST"])
def clockin():
    user_id = request.form.get("user_id")
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_record = Attendance(user_id=user_id, clock_in=time_now)
    db.session.add(new_record)
    db.session.commit()

    return redirect("/homepage")


# ===================== CLOCK OUT =======================
@app.route("/clockout", methods=["POST"])
def clockout():
    user_id = request.form.get("user_id")

    latest = Attendance.query.filter_by(user_id=user_id).order_by(Attendance.id.desc()).first()

    if latest:
        latest.clock_out = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.session.commit()

    return redirect("/homepage")

# ===================download csv====================

@app.route("/download_csv")
def download_csv():
    
    if "username" not in session:
        return redirect("/login")
    
    if session.get("role") != "admin":
        return "Access denied! Admin only.", 403

    users = User.query.all()

    csv_data = "user_id,username,email,role\n"
    for u in users:
        csv_data += f"{u.user_id},{u.username},{u.email},{u.role}\n"

    response = make_response(csv_data)
    response.headers["Content-Disposition"] = "attachment; filename=data_users.csv"
    response.headers["Content-Type"] = "text/csv"

    return response

# ======================= MAIN =======================
if __name__ == "__main__":
    with app.app_context():

        db.create_all()

        if not User.query.filter_by(username="admin").first():
            admin = User(
                username="admin",
                email="admin@gmail.com",
                password="123",
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created!")
        else:
            print("Admin existed")

    app.run(debug=True)


