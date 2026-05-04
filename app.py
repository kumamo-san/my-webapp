import csv
import os

from flask import Flask, redirect, url_for
from sqlalchemy import text
from sqlalchemy.orm import Session

from models import Department, Employee, engine

CSV_PATH = os.path.join(os.path.dirname(__file__), "employees.csv")


def _init_db():
    with engine.connect() as conn:
        # ── 1. departments テーブル作成 ───────────────────────────
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS departments (
                id               SERIAL PRIMARY KEY,
                department_code  VARCHAR(10)  UNIQUE NOT NULL,
                department_name  VARCHAR(100) NOT NULL
            )
        """))

        # ── 2. employees スキーマ移行（Stage 2 → 3） ─────────────
        cols = {r[0] for r in conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'employees'
        """))}

        if "department" in cols and "department_id" not in cols:
            # Stage 2 の department(VARCHAR) を department_id(FK) へ移行
            conn.execute(text(
                "ALTER TABLE employees ADD COLUMN department_id INTEGER"
            ))
            conn.commit()

            rows = conn.execute(text(
                "SELECT DISTINCT department FROM employees "
                "WHERE department IS NOT NULL ORDER BY department"
            )).fetchall()
            for i, (name,) in enumerate(rows, 1):
                conn.execute(text("""
                    INSERT INTO departments (department_code, department_name)
                    VALUES (:code, :name)
                    ON CONFLICT (department_code) DO NOTHING
                """), {"code": f"D{i:03d}", "name": name})
            conn.commit()

            conn.execute(text("""
                UPDATE employees e
                SET department_id = d.id
                FROM departments d
                WHERE e.department = d.department_name
            """))
            conn.execute(text(
                "ALTER TABLE employees "
                "ADD CONSTRAINT fk_employees_dept "
                "FOREIGN KEY (department_id) REFERENCES departments(id)"
            ))
            conn.execute(text("ALTER TABLE employees DROP COLUMN department"))

        elif "department_id" not in cols:
            conn.execute(text(
                "ALTER TABLE employees "
                "ADD COLUMN department_id INTEGER REFERENCES departments(id)"
            ))

        # ── 3. attendance テーブル作成 ────────────────────────────
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS attendance (
                id           SERIAL PRIMARY KEY,
                employee_id  INTEGER NOT NULL REFERENCES employees(id),
                work_date    DATE    NOT NULL,
                clock_in     TIME,
                clock_out    TIME,
                note         VARCHAR(200),
                UNIQUE(employee_id, work_date)
            )
        """))
        conn.commit()

    # ── 4. 初期データ投入（departments が空の場合のみ） ──────────
    with Session(engine) as session:
        if session.query(Department).count() == 0:
            dept_map: dict[str, Department] = {}
            with open(CSV_PATH, encoding="utf-8", newline="") as f:
                for row in csv.DictReader(f):
                    name = row["部署"]
                    if name not in dept_map:
                        d = Department(
                            department_code=f"D{len(dept_map)+1:03d}",
                            department_name=name,
                        )
                        session.add(d)
                        dept_map[name] = d
            session.flush()

            if session.query(Employee).count() == 0:
                with open(CSV_PATH, encoding="utf-8", newline="") as f:
                    for row in csv.DictReader(f):
                        session.add(Employee(
                            employee_id=row["社員番号"],
                            name=row["氏名"],
                            department=dept_map[row["部署"]],
                            position=row["役職"],
                            join_date=row["入社日"],
                        ))
            session.commit()


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-only-secret")

    _init_db()

    from blueprints.departments import bp as departments_bp
    from blueprints.employees import bp as employees_bp
    from blueprints.attendance import bp as attendance_bp

    app.register_blueprint(departments_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(attendance_bp)

    @app.route("/")
    def index():
        return redirect(url_for("employees.index"))

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
