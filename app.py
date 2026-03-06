from flask import Flask, render_template, request, redirect, url_for
import os
from sqlalchemy import create_engine, text

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

# HOME PAGE
@app.route("/")
def index():
    with engine.connect() as conn:
        players = conn.execute(text("SELECT * FROM players")).fetchall()

    player_data = []

    with engine.connect() as conn:
        for p in players:
            highest = conn.execute(
                text("""
                SELECT MAX(bid_amount)
                FROM bids
                WHERE player_id = :id
                """),
                {"id": p.id}
            ).scalar()

            if highest is None:
                highest = 0

            player_data.append({
                "id": p.id,
                "name": p.name,
                "country": p.country,
                "role": p.role,
                "highest_bid": highest
            })

    return render_template("index.html", players=player_data)


# PLAYER PAGE
@app.route("/player/<int:id>")
def player(id):
    with engine.connect() as conn:
        player = conn.execute(
            text("SELECT * FROM players WHERE id=:id"),
            {"id": id}
        ).fetchone()

        highest = conn.execute(
            text("SELECT MAX(bid_amount) FROM bids WHERE player_id=:id"),
            {"id": id}
        ).scalar()

    if highest is None:
        highest = 0

    return render_template("player.html", player=player, highest=highest)


# BID LOGIC
@app.route("/bid", methods=["POST"])
def bid():
    player_id = request.form["player_id"]
    bidder = request.form["bidder"]
    amount = int(request.form["bid_amount"])

    with engine.connect() as conn:

        current = conn.execute(
            text("""
            SELECT MAX(bid_amount)
            FROM bids
            WHERE player_id = :id
            """),
            {"id": player_id}
        ).scalar()

        if current is None:
            current = 0

        if amount <= current:
            return "Bid must be higher than current bid!"

        conn.execute(
            text("""
            INSERT INTO bids (player_id, bidder, bid_amount)
            VALUES (:player_id, :bidder, :amount)
            """),
            {
                "player_id": player_id,
                "bidder": bidder,
                "amount": amount
            }
        )

        conn.commit()

    return redirect(url_for("player", id=player_id))


if __name__ == "__main__":
    app.run(debug=True)
