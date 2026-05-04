from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy.orm import Session, joinedload

from models import Department, Employee, engine

bp = Blueprint("employees", __name__, url_prefix="/employees")


@bp.route("/")
def index():
    with Session(engine) as session:
        employees = (
            session.query(Employee)
            .options(joinedload(Employee.department))
            .order_by(Employee.employee_id)
            .all()
        )
        return render_template("employees/index.html", employees=employees)


@bp.route("/add", methods=["GET", "POST"])
def add():
    with Session(engine) as session:
        departments = (
            session.query(Department)
            .order_by(Department.department_code)
            .all()
        )
        if request.method == "POST":
            session.add(Employee(
                employee_id=request.form["employee_id"],
                name=request.form["name"],
                department_id=request.form.get("department_id") or None,
                position=request.form["position"],
                join_date=request.form["join_date"],
            ))
            session.commit()
            flash("社員を登録しました。", "success")
            return redirect(url_for("employees.index"))
        return render_template("employees/add.html", departments=departments)


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit(id):
    with Session(engine) as session:
        emp = session.get(Employee, id)
        if emp is None:
            flash("社員が見つかりません。", "error")
            return redirect(url_for("employees.index"))
        departments = (
            session.query(Department)
            .order_by(Department.department_code)
            .all()
        )
        if request.method == "POST":
            emp.employee_id   = request.form["employee_id"]
            emp.name          = request.form["name"]
            emp.department_id = request.form.get("department_id") or None
            emp.position      = request.form["position"]
            emp.join_date     = request.form["join_date"]
            session.commit()
            flash("社員情報を更新しました。", "success")
            return redirect(url_for("employees.index"))
        return render_template("employees/edit.html", employee=emp, departments=departments)


@bp.route("/<int:id>/delete", methods=["POST"])
def delete(id):
    with Session(engine) as session:
        emp = session.get(Employee, id)
        if emp:
            session.delete(emp)
            session.commit()
    flash("社員を削除しました。", "success")
    return redirect(url_for("employees.index"))
