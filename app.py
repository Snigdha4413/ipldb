from flask import Flask, render_template, request, redirect
from sqlalchemy import create_engine, text
import os

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

@app.route("/")
def index():
    with engine.connect() as conn:
        players = conn.execute(text("SELECT * FROM players")).fetchall()
    return render_template("index.html", players=players)

@app.route("/player/<int:id>")
def player(id):
    with engine.connect() as conn:
        player = conn.execute(text("SELECT * FROM players WHERE id=:id"), {"id":id}).fetchone()
    return render_template("player.html", player=player)

@app.route("/bid", methods=["POST"])
def bid():

    player_id = request.form["player_id"]
    bidder = request.form["bidder"]
    bid_amount = int(request.form["bid_amount"])

    with engine.connect() as conn:

        current = conn.execute(
            text("SELECT current_bid FROM players WHERE id=:id"),
            {"id":player_id}
        ).fetchone()

        if bid_amount > current[0]:

            conn.execute(text("""
            UPDATE players
            SET current_bid=:bid
            WHERE id=:id
            """), {"bid":bid_amount, "id":player_id})

            conn.execute(text("""
            INSERT INTO bids (player_id,bidder_name,bid_amount)
            VALUES (:pid,:bidder,:amount)
            """), {"pid":player_id,"bidder":bidder,"amount":bid_amount})

            conn.commit()

    return redirect("/")
    

if __name__ == "__main__":
    app.run(debug=True)
