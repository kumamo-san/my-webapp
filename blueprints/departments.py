from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy.orm import Session

from models import Department, Employee, engine

bp = Blueprint("departments", __name__, url_prefix="/departments")


@bp.route("/")
def index():
    with Session(engine) as session:
        departments = (
            session.query(Department)
            .order_by(Department.department_code)
            .all()
        )
        return render_template("departments/index.html", departments=departments)


@bp.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        with Session(engine) as session:
            session.add(Department(
                department_code=request.form["department_code"],
                department_name=request.form["department_name"],
            ))
            session.commit()
        flash("部署を登録しました。", "success")
        return redirect(url_for("departments.index"))
    return render_template("departments/add.html")


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit(id):
    with Session(engine) as session:
        dept = session.get(Department, id)
        if dept is None:
            flash("部署が見つかりません。", "error")
            return redirect(url_for("departments.index"))
        if request.method == "POST":
            dept.department_code = request.form["department_code"]
            dept.department_name = request.form["department_name"]
            session.commit()
            flash("部署情報を更新しました。", "success")
            return redirect(url_for("departments.index"))
        return render_template("departments/edit.html", department=dept)


@bp.route("/<int:id>/delete", methods=["POST"])
def delete(id):
    with Session(engine) as session:
        dept = session.get(Department, id)
        if dept is None:
            flash("部署が見つかりません。", "error")
            return redirect(url_for("departments.index"))
        emp_count = session.query(Employee).filter_by(department_id=id).count()
        if emp_count > 0:
            flash(f"この部署には {emp_count} 名の社員が所属しているため削除できません。", "error")
            return redirect(url_for("departments.index"))
        session.delete(dept)
        session.commit()
    flash("部署を削除しました。", "success")
    return redirect(url_for("departments.index"))
