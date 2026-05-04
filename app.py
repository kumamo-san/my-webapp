import csv
import os
from flask import Flask, render_template

app = Flask(__name__)

CSV_PATH = os.path.join(os.path.dirname(__file__), "employees.csv")


def load_employees():
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


@app.route("/")
def index():
    employees = load_employees()
    return render_template("index.html", employees=employees)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
