
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

@app.route("/compare")
def compare_resorts():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                
SELECT
    r.id,
    r.name,
    r.mountain,
    r.slopes_km,
    r.lifts_count,
    r.season_start,
    r.season_end,
    p.price_eur,
    p.season,
    p.pass_type
FROM resorts r
LEFT JOIN LATERAL (
    SELECT price_eur, season, pass_type
    FROM ski_pass_prices
    WHERE resort_id = r.id
      AND visitor_category = CASE
          WHEN r.name = 'Боровец' THEN 'Възрастни 23–64 г.'
          WHEN r.name = 'Пампорово' THEN 'Възрастни 22–64 г.'
          ELSE 'Възрастни'
      END
      AND pass_type = CASE
          WHEN r.name = 'Пампорово' THEN 'Цял ден Select'
          WHEN r.name = 'Витоша' THEN 'Алеко – 1 ден'
          ELSE 'Цял ден'
      END
    ORDER BY id DESC
    LIMIT 1
) p ON TRUE
WHERE r.name IN ('Банско', 'Боровец', 'Пампорово', 'Витоша')
ORDER BY r.name

            """)
            resorts = cursor.fetchall()

    return render_template("compare.html", resorts=resorts)



@app.route("/resorts/<int:resort_id>")
def resort_details(resort_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
            
                
SELECT id, name, mountain, description, image,
       ski_pass_price, slopes_km, lifts_count,
       season_start, season_end, difficulty,
       price_season, info_source,
       half_day_price, night_ski_price,
       price_validity, lifts_info, official_website,
       slopes_count, blue_slopes, red_slopes,
      
       black_slopes, longest_descent_km,
       cross_country_km
FROM resorts
WHERE id = %s



                """,
                (resort_id,)
            )
            resort = cur.fetchone()

    if resort is None:
        return "Курортът не е намерен.", 404

   
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT visitor_category, pass_type, price_eur,
                       season, valid_from, valid_to
                FROM ski_pass_prices
                WHERE resort_id = %s
                ORDER BY id
            """, (resort_id,))
            ski_pass_prices = cur.fetchall()

    return render_template(
        "resort_details.html",
        resort=resort,
        ski_pass_prices=ski_pass_prices
    )


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
