from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps
import os
from sqlalchemy import create_engine, text
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "ipl-auction-secret-key-2024")

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)


# --- AUTH HELPERS ---
def get_current_user():
    return session.get("user")

def is_admin():
    return session.get("role") == "admin"

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# --- LOGIN ---
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        with engine.connect() as conn:
            user = conn.execute(
                text("SELECT * FROM users WHERE username = :u"),
                {"u": username}
            ).fetchone()

        if user and check_password_hash(user.password, password):
            session["user"] = user.username
            session["role"] = user.role
            return redirect(url_for("index"))
        else:
            error = "Invalid username or password."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# --- HOME: Show Teams ---
@app.route("/")
@login_required
def index():
    with engine.connect() as conn:
        teams = conn.execute(
            text("SELECT DISTINCT team FROM players ORDER BY team")
        ).fetchall()

    return render_template("index.html", teams=teams,
                           user=get_current_user(), is_admin=is_admin())


# --- TEAM PAGE ---
@app.route("/team/<team_name>")
@login_required
def team(team_name):
    with engine.connect() as conn:
        players = conn.execute(
            text("SELECT * FROM players WHERE team = :team"),
            {"team": team_name}
        ).fetchall()

    player_data = []
    with engine.connect() as conn:
        for p in players:
            highest = conn.execute(
                text("SELECT MAX(bid_amount) FROM bids WHERE player_id = :id"),
                {"id": p.id}
            ).scalar() or 0

            top_bidder = conn.execute(
                text("""
                    SELECT bidder FROM bids
                    WHERE player_id = :id
                    ORDER BY bid_amount DESC LIMIT 1
                """),
                {"id": p.id}
            ).scalar()

            player_data.append({
                "id": p.id,
                "name": p.name,
                "country": p.country,
                "role": p.role,
                "team": p.team,
                "highest_bid": highest,
                "top_bidder": top_bidder or "No bids yet"
            })

    return render_template("team.html", players=player_data, team_name=team_name,
                           user=get_current_user(), is_admin=is_admin())


# --- PLAYER PAGE ---
@app.route("/player/<int:id>")
@login_required
def player(id):
    with engine.connect() as conn:
        p = conn.execute(
            text("SELECT * FROM players WHERE id = :id"), {"id": id}
        ).fetchone()

        highest = conn.execute(
            text("SELECT MAX(bid_amount) FROM bids WHERE player_id = :id"), {"id": id}
        ).scalar() or 0

        top_bidder = conn.execute(
            text("""
                SELECT bidder FROM bids
                WHERE player_id = :id
                ORDER BY bid_amount DESC LIMIT 1
            """),
            {"id": id}
        ).scalar()

        bid_history = conn.execute(
            text("""
                SELECT bidder, bid_amount, bid_time
                FROM bids WHERE player_id = :id
                ORDER BY bid_amount DESC
            """),
            {"id": id}
        ).fetchall()

    return render_template("player.html", player=p, highest=highest,
                           top_bidder=top_bidder, bid_history=bid_history,
                           user=get_current_user(), is_admin=is_admin())


# --- BID (Clients Only) ---
@app.route("/bid", methods=["POST"])
@login_required
def bid():
    if is_admin():
        return "Admins cannot place bids!", 403

    player_id = request.form["player_id"]
    bidder = session["user"]
    amount = int(request.form["bid_amount"])

    with engine.connect() as conn:
        current = conn.execute(
            text("SELECT MAX(bid_amount) FROM bids WHERE player_id = :id"),
            {"id": player_id}
        ).scalar() or 0

        if amount <= current:
            return f"Bid must be higher than current bid of ₹{current}!", 400

        conn.execute(
            text("""
                INSERT INTO bids (player_id, bidder, bid_amount)
                VALUES (:player_id, :bidder, :amount)
            """),
            {"player_id": player_id, "bidder": bidder, "amount": amount}
        )
        conn.commit()

    return redirect(url_for("player", id=player_id))


if __name__ == "__main__":
    app.run(debug=True)
