
from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import get_db_connection


app = Flask(
    __name__,
    template_folder="app/templates",
    static_folder="app/static"
)
app.json.ensure_ascii = False


@app.route("/")
def home():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, name, mountain, description, image "
                "FROM resorts ORDER BY id"
            )
            resorts = cursor.fetchall()

    return render_template("index.html", resorts=resorts)


@app.route("/resorts/add", methods=["POST"])
def add_resort():
    name = request.form.get("name", "").strip()
    mountain = request.form.get("mountain", "").strip()
    description = request.form.get("description", "").strip()

    if not name or not mountain:
        return "Името и планината са задължителни.", 400

    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO resorts (name, mountain, description, image)
                VALUES (%s, %s, %s, %s)
                """,
                (name, mountain, description, "default.jpg")
            )
        conn.commit()
    finally:
        conn.close()

    return redirect(url_for("home") + "#resorts")

@app.route("/resorts/<int:resort_id>/edit", methods=["GET", "POST"])
def edit_resort(resort_id):
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            if request.method == "POST":
                name = request.form.get("name", "").strip()
                mountain = request.form.get("mountain", "").strip()
                description = request.form.get("description", "").strip()

                if not name or not mountain:
                    return "Името и планината са задължителни.", 400

                cur.execute(
                    """
                    UPDATE resorts
                    SET name = %s, mountain = %s, description = %s
                    WHERE id = %s
                    """,
                    (name, mountain, description, resort_id)
                )
                conn.commit()

                return redirect(url_for("home") + "#resorts")

            cur.execute(
                """
                SELECT id, name, mountain, description
                FROM resorts
                WHERE id = %s
                """,
                (resort_id,)
            )
            resort = cur.fetchone()

            if resort is None:
                return "Курортът не е намерен.", 404

            return render_template("edit_resort.html", resort=resort)

    finally:
        conn.close()

@app.route("/resorts/<int:resort_id>/delete", methods=["POST"])
def delete_resort(resort_id):
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM resorts WHERE id = %s",
                (resort_id,)
            )
        conn.commit()
    finally:
        conn.close()

    return redirect(url_for("home") + "#resorts")

@app.route("/api/resorts", methods=["GET"])
def api_get_resorts():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, mountain, description, image
                FROM resorts
                ORDER BY id
                """
            )
            rows = cur.fetchall()

    resorts = [
        {
            "id": row[0],
            "name": row[1],
            "mountain": row[2],
            "description": row[3],
            "image": row[4]
        }
        for row in rows
    ]

    return jsonify(resorts)


@app.route("/api/resorts/<int:resort_id>", methods=["GET"])
def api_get_resort(resort_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, mountain, description, image
                FROM resorts
                WHERE id = %s
                """,
                (resort_id,)
            )
            row = cur.fetchone()

    if row is None:
        return jsonify({
            "error": "Курортът не е намерен."
        }), 404

    resort = {
        "id": row[0],
        "name": row[1],
        "mountain": row[2],
        "description": row[3],
        "image": row[4]
    }

    return jsonify(resort)

@app.route("/api/resorts", methods=["POST"])
def api_add_resort():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Невалидни JSON данни."
        }), 400

    name = data.get("name")
    mountain = data.get("mountain")
    description = data.get("description", "")

    if (
        not isinstance(name, str)
        or not name.strip()
        or not isinstance(mountain, str)
        or not mountain.strip()
        or not isinstance(description, str)
    ):
        return jsonify({
            "error": "Името и планината са задължителни."
        }), 400

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO resorts (name, mountain, description, image)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (
                    name.strip(),
                    mountain.strip(),
                    description.strip(),
                    "default.jpg"
                )
            )
            resort_id = cur.fetchone()[0]

    return jsonify({
        "id": resort_id,
        "name": name.strip(),
        "mountain": mountain.strip(),
        "description": description.strip(),
        "image": "default.jpg"
    }), 201

@app.route("/api/resorts/<int:resort_id>", methods=["PUT"])
def api_update_resort(resort_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Невалидни JSON данни."}), 400

    name = data.get("name")
    mountain = data.get("mountain")
    description = data.get("description", "")

    if (
        not isinstance(name, str)
        or not name.strip()
        or not isinstance(mountain, str)
        or not mountain.strip()
        or not isinstance(description, str)
    ):
        return jsonify({
            "error": "Името и планината са задължителни."
        }), 400

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE resorts
                SET name = %s,
                    mountain = %s,
                    description = %s
                WHERE id = %s
                RETURNING id, name, mountain, description, image
                """,
                (
                    name.strip(),
                    mountain.strip(),
                    description.strip(),
                    resort_id
                )
            )
            row = cur.fetchone()

    if row is None:
        return jsonify({
            "error": "Курортът не е намерен."
        }), 404

    return jsonify({
        "id": row[0],
        "name": row[1],
        "mountain": row[2],
        "description": row[3],
        "image": row[4]
    })


@app.route("/api/resorts/<int:resort_id>", methods=["DELETE"])
def api_delete_resort(resort_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM resorts
                WHERE id = %s
                RETURNING id
                """,
                (resort_id,)
            )
            deleted = cur.fetchone()

    if deleted is None:
        return jsonify({
            "error": "Курортът не е намерен."
        }), 404

    return "", 204

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
