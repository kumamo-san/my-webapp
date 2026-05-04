import csv
import os

from flask import Flask, flash, redirect, render_template, request, url_for
from google.cloud.sql.connector import Connector
import sqlalchemy
from sqlalchemy import text

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-secret")

INSTANCE_CONNECTION_NAME = os.environ.get("INSTANCE_CONNECTION_NAME", "")
DB_USER = os.environ.get("DB_USER", "")
DB_PASS = os.environ.get("DB_PASS", "")
DB_NAME = os.environ.get("DB_NAME", "")

_connector = Connector()


def _getconn():
    return _connector.connect(
        INSTANCE_CONNECTION_NAME,
        "pg8000",
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME,
    )


engine = sqlalchemy.create_engine("postgresql+pg8000://", creator=_getconn)

CSV_PATH = os.path.join(os.path.dirname(__file__), "employees.csv")


def init_db():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS employees (
                id          SERIAL PRIMARY KEY,
                employee_id VARCHAR(10)  UNIQUE NOT NULL,
                name        VARCHAR(100) NOT NULL,
                department  VARCHAR(100) NOT NULL,
                position    VARCHAR(100) NOT NULL,
                join_date   DATE         NOT NULL
            )
        """))
        conn.commit()

        count = conn.execute(text("SELECT COUNT(*) FROM employees")).scalar()
        if count == 0:
            with open(CSV_PATH, encoding="utf-8", newline="") as f:
                for row in csv.DictReader(f):
                    conn.execute(text("""
                        INSERT INTO employees (employee_id, name, department, position, join_date)
                        VALUES (:eid, :name, :dept, :pos, :jd)
                        ON CONFLICT (employee_id) DO NOTHING
                    """), {
                        "eid": row["社員番号"],
                        "name": row["氏名"],
                        "dept": row["部署"],
                        "pos": row["役職"],
                        "jd": row["入社日"],
                    })
            conn.commit()


with app.app_context():
    init_db()


@app.route("/")
def index():
    with engine.connect() as conn:
        employees = conn.execute(text(
            "SELECT id, employee_id, name, department, position, join_date "
            "FROM employees ORDER BY employee_id"
        )).mappings().all()
    return render_template("index.html", employees=employees)


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO employees (employee_id, name, department, position, join_date)
                VALUES (:eid, :name, :dept, :pos, :jd)
            """), {
                "eid": request.form["employee_id"],
                "name": request.form["name"],
                "dept": request.form["department"],
                "pos": request.form["position"],
                "jd": request.form["join_date"],
            })
            conn.commit()
        flash("社員を登録しました。", "success")
        return redirect(url_for("index"))
    return render_template("add.html")


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if request.method == "POST":
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE employees
                SET employee_id=:eid, name=:name, department=:dept,
                    position=:pos, join_date=:jd
                WHERE id=:id
            """), {
                "id": id,
                "eid": request.form["employee_id"],
                "name": request.form["name"],
                "dept": request.form["department"],
                "pos": request.form["position"],
                "jd": request.form["join_date"],
            })
            conn.commit()
        flash("社員情報を更新しました。", "success")
        return redirect(url_for("index"))

    with engine.connect() as conn:
        employee = conn.execute(text(
            "SELECT id, employee_id, name, department, position, join_date "
            "FROM employees WHERE id=:id"
        ), {"id": id}).mappings().first()

    if employee is None:
        flash("社員が見つかりません。", "error")
        return redirect(url_for("index"))
    return render_template("edit.html", employee=employee)


@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM employees WHERE id=:id"), {"id": id})
        conn.commit()
    flash("社員を削除しました。", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
