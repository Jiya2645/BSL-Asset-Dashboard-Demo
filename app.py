from flask import send_file
import pandas as pd
from io import BytesIO
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
import pandas as pd

EXCEL_FILE = "PC PRINTER MFD SCANNER DETAILS 17 04 2026 - Copy.xlsx"

def load_department_totals():
    
    totals = {}

    sheet_config = {

        "PC DETAILS": "TOTAL",
        "PRINTER DETAIL": "TOTAL",
        "MFD DETAIL": "TOTAL",
        "SCANNER DETAILS": "TOTAL"

    }

    for sheet, total_column in sheet_config.items():

        df = pd.read_excel(
    EXCEL_FILE,
    sheet_name=sheet,
    header=2
)
        print("\n")
        print(sheet)
        print(df.columns.tolist())

        dept_col = df.columns[1]

        actual_total_col = None

        for col in df.columns:

            if "TOTAL" in str(col).upper():

                actual_total_col = col
                break

        if actual_total_col is None:
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
                row[actual_total_col],
                errors="coerce"
            )

            if pd.isna(count):
                continue

            dept = dept.upper()

            totals[dept] = (
                totals.get(dept, 0)
                + int(count)
            )

    print("GRAND TOTAL =", sum(totals.values()))

    return totals

app = Flask(__name__)
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
    DEPARTMENT_TOTALS = load_department_totals()
   

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
    location = request.args.get(
    "location",
    ""
).strip()
    pc_make = request.args.get(
    "pc_make",
    ""
).strip()
    if department:

        assets = [

            a for a in assets

            if str(
                a.get("Deptt.", "")
            ).strip() == department
        ]

    tagged = len(assets)

    dept_lookup = {

    str(k).strip().upper(): v

    for k, v in DEPARTMENT_TOTALS.items()
}

    if department:

      total = dept_lookup.get(
        department.strip().upper(),
        tagged
    )

    else:

      total = 2230

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

    return jsonify({

        "locations":
        len(locations),

        "pc_makes":
        len(pc_makes)

    })
if __name__ == "__main__":
    app.run(debug=True)