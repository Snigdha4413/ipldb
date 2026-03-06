from flask import Flask, render_template, request
import os
from sqlalchemy import create_engine

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})

@app.route("/")
def index():
    return "Server is working!"

@app.route("/")
def index():

    conn = engine.connect()

    result = conn.execute("SELECT * FROM players")

    players = result.fetchall()

    return render_template("index.html", players=players)


@app.route('/bid', methods=['POST'])
def bid():

    player_id = request.form['player_id']
    bid_amount = int(request.form['bid'])

    conn = engine.connect()

    result = conn.execute(
        f"SELECT current_price FROM players WHERE id={player_id}"
    ).fetchone()

    current_price = result[0]

    if bid_amount > current_price:

        conn.execute(
            f"UPDATE players SET current_price={bid_amount} WHERE id={player_id}"
        )

        message = "Bid accepted!"

    else:
        message = "Bid must be higher than current price"

    players = conn.execute("SELECT * FROM players").fetchall()

    return render_template("index.html", players=players, message=message)


if __name__ == "__main__":

    app.run(debug=True)



