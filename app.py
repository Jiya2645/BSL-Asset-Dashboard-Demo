from flask import send_file
import pandas as pd
from io import BytesIO
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
import pandas as pd

EXCEL_FILE = "PC PRINTER MFD SCANNER DETAILS 17 04 2026 - Copy.xlsx"
PC_TOTALS = {}
PRINTER_TOTALS = {}
MFD_TOTALS = {}
SCANNER_TOTALS = {}
def load_department_totals():
    
    global PC_TOTALS
    global PRINTER_TOTALS
    global MFD_TOTALS
    global SCANNER_TOTALS

    PC_TOTALS = {}
    PRINTER_TOTALS = {}
    MFD_TOTALS = {}
    SCANNER_TOTALS = {}

    sheet_map = {

        "PC DETAILS": PC_TOTALS,
        "PRINTER DETAIL": PRINTER_TOTALS,
        "MFD DETAIL": MFD_TOTALS,
        "SCANNER DETAILS": SCANNER_TOTALS

    }

    for sheet, target_dict in sheet_map.items():

        df = pd.read_excel(
            EXCEL_FILE,
            sheet_name=sheet,
            header=2
        )

        dept_col = df.columns[1]

        total_col = None

        for col in df.columns:

            if "TOTAL" in str(col).upper():

                total_col = col
                break

        if total_col is None:
            continue

        for _, row in df.iterrows():

            dept = str(
                row[dept_col]
            ).strip()

            if (
                dept == "" or
                dept.lower() == "nan" or
                "TOTAL" in dept.upper() or
                dept.upper() == "DEPTT."
            ):
                continue

            count = pd.to_numeric(
                row[total_col],
                errors="coerce"
            )

            if pd.isna(count):
                continue

            target_dict[
                dept.upper()
            ] = int(count)

    return True
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
app.secret_key = "bsl_asset_dashboard_2030_secret"

# ---------------------------
# Load Asset Data
# ---------------------------

DATA_FILE = os.path.join(
    os.path.dirname(__file__),
    "assets_data.json"
)

with open(DATA_FILE, "r", encoding="utf-8") as f:

    ALL_ASSETS = json.load(f)

load_department_totals()
   

# ---------------------------
# Demo Users
# ---------------------------

USERS = {
    "ADMIN001": {
        "password": "1234",
        "role": "ADMIN",
        "department": "ALL",
        "name": "Administrator"
    },

    "HOD001": {
        "password": "1234",
        "role": "HOD",
        "department": "IT",
        "name": "IT HOD"
    },

    "EMP001": {
        "password": "1234",
        "role": "STAFF",
        "department": "IT",
        "staff_no": "779986",
        "name": "Employee"
    }
}


# ---------------------------
# Role Based Asset Access
# ---------------------------

def get_assets_for_user(user):

    role = user["role"]

    if role == "ADMIN":
        return ALL_ASSETS

    elif role == "HOD":

        department = user["department"]

        return [
            asset
            for asset in ALL_ASSETS
            if str(asset.get("Deptt.", "")).strip().upper()
            == department.upper()
        ]

    elif role == "STAFF":

        staff_no = str(user.get("staff_no", ""))

        return [
            asset
            for asset in ALL_ASSETS
            if str(asset.get("Staff No.", "")).strip()
            == staff_no
        ]

    return []


# ---------------------------
# Home Page
# ---------------------------

@app.route("/")
def home():

    if "user" in session:
        return redirect(url_for("dashboard"))

    return render_template("index.html")


# ---------------------------
# Login
# ---------------------------

@app.route("/login", methods=["POST"])
def login():

    employee_id = request.form.get(
        "employee_id",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    ).strip()

    if (
        employee_id in USERS and
        USERS[employee_id]["password"] == password
    ):

        user = USERS[employee_id].copy()
        user["employee_id"] = employee_id

        session["user"] = user

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "index.html",
        error="Invalid ID or Password"
    )


# ---------------------------
# Logout
# ---------------------------

@app.route("/logout")
def logout():

    session.pop("user", None)

    return redirect(
        url_for("home")
    )


# ---------------------------
# Dashboard
# ---------------------------

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect(url_for("home"))

    return render_template(
        "dashboard.html",
        user=session["user"]
    )


# ---------------------------
# Statistics API
# ---------------------------

@app.route("/api/stats")
def stats():

    if "user" not in session:
        return jsonify(
            {"error": "Unauthorized"}
        ), 401

    assets = get_assets_for_user(
        session["user"]
    )

    total = len(assets)

    tagged = sum(
    1
    for asset in assets
    if str(
        asset.get(
            "LOT ID",
            ""
        )
    ).strip() != ""
)

    pending = total - tagged

    dept_counts = {}

    for asset in assets:

        dept = str(
            asset.get(
                "Deptt.",
                "Unknown"
            )
        ).strip()

        dept_counts[dept] = (
            dept_counts.get(dept, 0) + 1
        )

    pc_counts = {}

    for asset in assets:

        pc_make = str(
            asset.get(
                "PC Make",
                "Unknown"
            )
        ).strip()

        if pc_make:

            pc_counts[pc_make] = (
                pc_counts.get(pc_make, 0) + 1
            )
    return jsonify({

        "total": total,

        "tagged": tagged,

        "pending": pending,

        "dept_counts": dept_counts,

        "pc_counts": pc_counts
    })


# ---------------------------
# Assets API
# ---------------------------
@app.route("/api/department-summary")
def department_summary():

    department = request.args.get(
        "department",
        ""
    ).strip()

    assets = get_assets_for_user(
        session["user"]
    )

    if department:

        assets = [

            a for a in assets

            if str(
                a.get("Deptt.", "")
            ).strip() == department

        ]

    pc_tagged = sum(
        1 for a in assets
        if str(a.get("LOT ID", "")).strip()
    )

    printer_tagged = sum(
        1 for a in assets
        if str(a.get("PRINTER LOT ID", "")).strip()
    )

    mfd_tagged = sum(
        1 for a in assets
        if str(a.get("MFD LOT ID", "")).strip()
    )

    scanner_tagged = sum(
        1 for a in assets
        if str(a.get("SCANNER LOT ID", "")).strip()
    )

    tagged = (
        pc_tagged +
        printer_tagged +
        mfd_tagged +
        scanner_tagged
    )

    if department:

        dept_key = department.upper()

        total = (
            PC_TOTALS.get(dept_key, 0)
            + PRINTER_TOTALS.get(dept_key, 0)
            + MFD_TOTALS.get(dept_key, 0)
            + SCANNER_TOTALS.get(dept_key, 0)
        )

    else:

        total = (
            sum(PC_TOTALS.values())
            + sum(PRINTER_TOTALS.values())
            + sum(MFD_TOTALS.values())
            + sum(SCANNER_TOTALS.values())
        )

    pending = max(
        total - tagged,
        0
    )

    completion = round(
        (tagged / total) * 100,
        1
    ) if total else 0

    return jsonify({

        "total": total,
        "tagged": tagged,
        "pending": pending,
        "completion": completion

    })
@app.route("/employees")
def employees():

    if "user" not in session:
        return redirect(url_for("home"))

    return render_template(
        "employees.html",
        user=session["user"]
    )
@app.route("/departments")
def departments():

    if "user" not in session:
        return redirect(url_for("home"))

    return render_template(
        "departments.html",
        user=session["user"]
    )
@app.route("/api/department-report")
def department_report():

    report = []

    departments = set()

    departments.update(PC_TOTALS.keys())
    departments.update(PRINTER_TOTALS.keys())
    departments.update(MFD_TOTALS.keys())
    departments.update(SCANNER_TOTALS.keys())

    for dept in sorted(departments):

        total = (
            PC_TOTALS.get(dept, 0)
            + PRINTER_TOTALS.get(dept, 0)
            + MFD_TOTALS.get(dept, 0)
            + SCANNER_TOTALS.get(dept, 0)
        )

        assets = [

            a for a in ALL_ASSETS

            if str(
                a.get("Deptt.", "")
            ).strip().upper() == dept

        ]

        tagged = 0

        for asset in assets:

            if str(asset.get("LOT ID", "")).strip():
                tagged += 1

            if str(asset.get("PRINTER LOT ID", "")).strip():
                tagged += 1

            if str(asset.get("MFD LOT ID", "")).strip():
                tagged += 1

            if str(asset.get("SCANNER LOT ID", "")).strip():
                tagged += 1

        untagged = max(total - tagged, 0)

        completion = round(
            (tagged / total) * 100,
            1
        ) if total else 0

        report.append({

            "department": dept,
            "total": total,
            "tagged": tagged,
            "untagged": untagged,
            "completion": completion

        })

    return jsonify(report)
@app.route("/api/employees")
def employees_api():

    assets = get_assets_for_user(
        session["user"]
    )

    return jsonify(assets)
@app.route("/analytics")
def analytics():

    if "user" not in session:
        return redirect(url_for("home"))

    return render_template(
        "analytics.html",
        user=session["user"]
    )
@app.route("/api/analytics")
def analytics_api():

    report = department_report().json

    return jsonify(report)
@app.route("/api/assets")
def assets():

    if "user" not in session:
        return jsonify(
            {"error": "Unauthorized"}
        ), 401

    assets = get_assets_for_user(
        session["user"]
    )

    search = request.args.get(
        "search",
        ""
    ).lower()

    if search:

        assets = [

            asset

            for asset in assets

            if (
                search in str(
                    asset.get(
                        "Name",
                        ""
                    )
                ).lower()

                or

                search in str(
                    asset.get(
                        "Staff No.",
                        ""
                    )
                ).lower()

                or

                search in str(
                    asset.get(
                        "HOST NAME",
                        ""
                    )
                ).lower()

                or

                search in str(
                    asset.get(
                        "Deptt.",
                        ""
                    )
                ).lower()
            )
        ]

    return jsonify(assets)

# ---------------------------
# Filters API
# ---------------------------

@app.route("/api/filters")
def filters():

    if "user" not in session:
        return jsonify(
            {"error": "Unauthorized"}
        ), 401

    assets = get_assets_for_user(
        session["user"]
    )

    departments = sorted(

        list(

            set(

                str(
                    asset.get(
                        "Deptt.",
                        ""
                    )
                ).strip()

                for asset in assets

                if asset.get(
                    "Deptt.",
                    ""
                )
            )
        )
    )

    locations = sorted(

        list(

            set(

                str(
                    asset.get(
                        "Location",
                        ""
                    )
                ).strip()

                for asset in assets

                if asset.get(
                    "Location",
                    ""
                )
            )
        )
    )

    pc_makes = sorted(

        list(

            set(

                str(
                    asset.get(
                        "PC Make",
                        ""
                    )
                ).strip()

                for asset in assets

                if asset.get(
                    "PC Make",
                    ""
                )
            )
        )
    )

    return jsonify({

        "departments": departments,

        "locations": locations,

        "pc_makes": pc_makes
    })


# ---------------------------
# Run Flask
# ---------------------------
# ---------------------------
# Export Excel
# ---------------------------

@app.route("/export")
def export_excel():

    if "user" not in session:
        return redirect(url_for("home"))

    assets = get_assets_for_user(
        session["user"]
    )

    df = pd.DataFrame(assets)

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Assets"
        )

    output.seek(0)

    return send_file(

        output,

        as_attachment=True,

        download_name=
        "BSL_Assets_Report.xlsx",

        mimetype=
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
@app.route('/api/dashboard-metrics')
def dashboard_metrics():

    locations = set()
    pc_makes = set()
    departments = set()

    assets = get_assets_for_user(
        session["user"]
    )

    for asset in assets:

        locations.add(
            asset.get(
                "Location",
                ""
            )
        )

        pc_makes.add(
            asset.get(
                "PC Make",
                ""
            )
        )

        departments.add(
            asset.get(
                "Deptt.",
                ""
            )
        )

    return jsonify({

        "locations":
        len(locations),

        "pc_makes":
        len(pc_makes),

        "departments":
        len(departments)

    })
@app.route("/api/asset-breakdown")
def asset_breakdown():

    department = request.args.get(
        "department",
        ""
    ).strip()

    assets = get_assets_for_user(
        session["user"]
    )

    if department:

        assets = [

            a for a in assets

            if str(
                a.get("Deptt.", "")
            ).strip() == department

        ]

    pc_tagged = 0
    printer_tagged = 0
    mfd_tagged = 0
    scanner_tagged = 0

    for asset in assets:

        if str(asset.get("LOT ID", "")).strip():
            pc_tagged += 1

        if str(asset.get("PRINTER LOT ID", "")).strip():
            printer_tagged += 1

        if str(asset.get("MFD LOT ID", "")).strip():
            mfd_tagged += 1

        if str(asset.get("SCANNER LOT ID", "")).strip():
            scanner_tagged += 1

    dept_key = department.upper()

    pc_total = PC_TOTALS.get(
        dept_key,
        3360 if not department else 0
    )

    printer_total = PRINTER_TOTALS.get(
        dept_key,
        941 if not department else 0
    )

    mfd_total = MFD_TOTALS.get(
        dept_key,
        170 if not department else 0
    )

    scanner_total = SCANNER_TOTALS.get(
        dept_key,
        486 if not department else 0
    )

    return jsonify({

        "pc": {
            "total": pc_total,
            "tagged": pc_tagged,
            "untagged": max(pc_total - pc_tagged, 0)
        },

        "printer": {
            "total": printer_total,
            "tagged": printer_tagged,
            "untagged": max(printer_total - printer_tagged, 0)
        },

        "mfd": {
            "total": mfd_total,
            "tagged": mfd_tagged,
            "untagged": max(mfd_total - mfd_tagged, 0)
        },

        "scanner": {
            "total": scanner_total,
            "tagged": scanner_tagged,
            "untagged": max(scanner_total - scanner_tagged, 0)
        }


    })
if __name__ == "__main__":
    app.run(debug=True)