import calendar
from collections import defaultdict
from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy.orm import Session, joinedload

from models import Attendance, Employee, engine

bp = Blueprint("attendance", __name__, url_prefix="/attendance")


@bp.route("/")
def index():
    employee_id    = request.args.get("employee_id", type=int)
    selected_month = request.args.get("month", date.today().strftime("%Y-%m"))

    with Session(engine) as session:
        employees = (
            session.query(Employee)
            .order_by(Employee.employee_id)
            .all()
        )

        q = (
            session.query(Attendance)
            .options(joinedload(Attendance.employee).joinedload(Employee.department))
            .order_by(Attendance.work_date.desc(), Attendance.employee_id)
        )
        if employee_id:
            q = q.filter(Attendance.employee_id == employee_id)
        if selected_month:
            year, mon = map(int, selected_month.split("-"))
            first = date(year, mon, 1)
            last  = date(year, mon, calendar.monthrange(year, mon)[1])
            q = q.filter(Attendance.work_date.between(first, last))

        records = q.all()

        # 月次集計
        summary_map: dict = defaultdict(lambda: {"employee": None, "days": 0, "hours": 0.0})
        for r in records:
            s = summary_map[r.employee_id]
            s["employee"] = r.employee
            s["days"] += 1
            if r.work_hours is not None:
                s["hours"] = round(s["hours"] + r.work_hours, 1)
        summary = sorted(
            summary_map.values(),
            key=lambda x: x["employee"].employee_id,
        )

        return render_template(
            "attendance/index.html",
            records=records,
            employees=employees,
            summary=summary,
            selected_employee_id=employee_id,
            selected_month=selected_month,
        )


@bp.route("/add", methods=["GET", "POST"])
def add():
    with Session(engine) as session:
        employees = (
            session.query(Employee)
            .order_by(Employee.employee_id)
            .all()
        )
        if request.method == "POST":
            session.add(Attendance(
                employee_id=request.form["employee_id"],
                work_date=request.form["work_date"],
                clock_in=request.form.get("clock_in") or None,
                clock_out=request.form.get("clock_out") or None,
                note=request.form.get("note") or None,
            ))
            session.commit()
            flash("勤怠を登録しました。", "success")
            return redirect(url_for("attendance.index"))
        return render_template(
            "attendance/add.html",
            employees=employees,
            today=date.today().isoformat(),
        )


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit(id):
    with Session(engine) as session:
        record = session.get(Attendance, id)
        if record is None:
            flash("勤怠データが見つかりません。", "error")
            return redirect(url_for("attendance.index"))
        employees = (
            session.query(Employee)
            .order_by(Employee.employee_id)
            .all()
        )
        if request.method == "POST":
            record.employee_id = request.form["employee_id"]
            record.work_date   = request.form["work_date"]
            record.clock_in    = request.form.get("clock_in") or None
            record.clock_out   = request.form.get("clock_out") or None
            record.note        = request.form.get("note") or None
            session.commit()
            flash("勤怠を更新しました。", "success")
            return redirect(url_for("attendance.index"))
        return render_template("attendance/edit.html", record=record, employees=employees)


@bp.route("/<int:id>/delete", methods=["POST"])
def delete(id):
    with Session(engine) as session:
        record = session.get(Attendance, id)
        if record:
            session.delete(record)
            session.commit()
    flash("勤怠を削除しました。", "success")
    return redirect(url_for("attendance.index"))
