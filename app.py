import os
import secrets
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "reservations.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.environ.get("SECRET_KEY", "dev-key")

db = SQLAlchemy(app)

SEAT_COLUMNS = ["A", "B", "C", "D"]


def get_cost_matrix():
    return [[100, 75, 50, 100] for _ in range(12)]


class Reservation(db.Model):
    __tablename__ = "reservations"

    id = db.Column(db.Integer, primary_key=True)
    passengerName = db.Column(db.String, nullable=False)
    seatRow = db.Column(db.Integer, nullable=False)
    seatColumn = db.Column(db.Integer, nullable=False)
    eTicketNumber = db.Column(db.String, nullable=False)
    created = db.Column(db.DateTime, server_default=db.func.now())


class Admin(db.Model):
    __tablename__ = "admins"

    username = db.Column(db.String, primary_key=True)
    password = db.Column(db.String, nullable=False)


def seat_label(row_index: int, col_index: int) -> str:
    return f"{row_index + 1}{SEAT_COLUMNS[col_index]}"


def build_seating_chart():
    reservations = Reservation.query.all()
    taken = {(r.seatRow, r.seatColumn) for r in reservations}
    chart = []
    for row_index in range(12):
        seats = []
        for col_index in range(4):
            seats.append(
                {"label": seat_label(row_index, col_index), "taken": (row_index, col_index) in taken}
            )
        chart.append({"row_number": row_index + 1, "seats": seats})
    return chart


def total_sales():
    prices = get_cost_matrix()
    total = 0
    for res in Reservation.query.all():
        if 0 <= res.seatRow < 12 and 0 <= res.seatColumn < 4:
            total += prices[res.seatRow][res.seatColumn]
    return total


def generate_ticket_code(name: str, row_index: int, col_index: int) -> str:
    prefix = "".join(name.split())[:3].upper() or "TRP"
    unique = secrets.token_hex(3).upper()
    return f"{prefix}{unique}{row_index + 1}{SEAT_COLUMNS[col_index]}"


@app.route("/", methods=["GET", "POST"])
def index():
    message = None
    if request.method == "POST":
        choice = request.form.get("menu_option")
        if choice == "reserve":
            return redirect(url_for("reserve"))
        if choice == "admin":
            return redirect(url_for("admin"))
        message = "pick an option."

    chart = build_seating_chart()
    return render_template("index.html", chart=chart, message=message)


@app.route("/reserve", methods=["GET", "POST"])
def reserve():
    error = None
    success = None
    ticket_code = None

    if request.method == "POST":
        first = request.form.get("first_name", "").strip()
        last = request.form.get("last_name", "").strip()
        seat_row = request.form.get("seat_row", "")
        seat_col = request.form.get("seat_col", "")

        try:
            row_index = int(seat_row) - 1
            col_index = int(seat_col) - 1
        except ValueError:
            row_index = col_index = -1

        taken = Reservation.query.filter_by(seatRow=row_index, seatColumn=col_index).first()

        if not first or not last:
            error = "please enter first and last name."
        elif row_index not in range(12) or col_index not in range(4):
            error = "pick a seat within the chart."
        elif taken:
            error = "seat already reserved."
        else:
            full_name = f"{first} {last}"
            ticket_code = generate_ticket_code(full_name, row_index, col_index)
            while Reservation.query.filter_by(eTicketNumber=ticket_code).first():
                ticket_code = generate_ticket_code(full_name, row_index, col_index)

            new_res = Reservation(
                passengerName=full_name,
                seatRow=row_index,
                seatColumn=col_index,
                eTicketNumber=ticket_code,
            )
            db.session.add(new_res)
            db.session.commit()
            success = f"seat {seat_label(row_index, col_index)} booked."

    chart = build_seating_chart()
    return render_template(
        "reserve.html",
        chart=chart,
        error=error,
        success=success,
        ticket_code=ticket_code,
    )


@app.route("/admin", methods=["GET", "POST"])
def admin():
    login_error = None
    message = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        action = request.form.get("action", "")
        admin_user = Admin.query.filter_by(username=username, password=password).first()

        if not admin_user:
            login_error = "invalid credentials."
            return render_template("admin.html", login=True, error=login_error)

        if action == "delete":
            res_id = request.form.get("reservation_id")
            res = Reservation.query.get(res_id)
            if res:
                db.session.delete(res)
                db.session.commit()
                message = "reservation removed."
            else:
                message = "reservation not found."

        reservations = Reservation.query.order_by(Reservation.created.desc()).all()
        chart = build_seating_chart()
        sales = total_sales()
        creds = {"username": username, "password": password}
        return render_template(
            "admin.html",
            login=False,
            chart=chart,
            reservations=reservations,
            sales=sales,
            message=message,
            admin_creds=creds,
        )

    return render_template("admin.html", login=True, error=login_error)


if __name__ == "__main__":
    app.run(debug=True)

