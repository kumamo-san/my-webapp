import os
from datetime import date, datetime

from google.cloud.sql.connector import Connector
import sqlalchemy
from sqlalchemy import Column, ForeignKey, Integer, String, Date, Time, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, relationship

_connector = Connector()


def _getconn():
    return _connector.connect(
        os.environ.get("INSTANCE_CONNECTION_NAME", ""),
        "pg8000",
        user=os.environ.get("DB_USER", ""),
        password=os.environ.get("DB_PASS", ""),
        db=os.environ.get("DB_NAME", ""),
    )


engine = sqlalchemy.create_engine("postgresql+pg8000://", creator=_getconn)


class Base(DeclarativeBase):
    pass


class Department(Base):
    __tablename__ = "departments"

    id              = Column(Integer, primary_key=True)
    department_code = Column(String(10), unique=True, nullable=False)
    department_name = Column(String(100), nullable=False)

    employees = relationship("Employee", back_populates="department")


class Employee(Base):
    __tablename__ = "employees"

    id            = Column(Integer, primary_key=True)
    employee_id   = Column(String(10), unique=True, nullable=False)
    name          = Column(String(100), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"))
    position      = Column(String(100), nullable=False)
    join_date     = Column(Date, nullable=False)

    department  = relationship("Department", back_populates="employees")
    attendances = relationship(
        "Attendance", back_populates="employee", cascade="all, delete-orphan"
    )


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (UniqueConstraint("employee_id", "work_date"),)

    id          = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    work_date   = Column(Date, nullable=False)
    clock_in    = Column(Time)
    clock_out   = Column(Time)
    note        = Column(String(200))

    employee = relationship("Employee", back_populates="attendances")

    @property
    def work_hours(self):
        if self.clock_in and self.clock_out:
            delta = (
                datetime.combine(self.work_date, self.clock_out)
                - datetime.combine(self.work_date, self.clock_in)
            )
            return round(delta.total_seconds() / 3600, 1)
        return None
