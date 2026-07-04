import random
from flask import Flask, request, jsonify, render_template, session
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'miranda-games-secret')

DB_PATH = os.path.join(os.path.dirname(__file__), 'games.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def migrate_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dice_roll (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT    NOT NULL,
            die1        INTEGER NOT NULL,
            die2        INTEGER NOT NULL,
            rolled_at   DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/dice')
def dice():
    return render_template('dice.html')


@app.route('/api/dice/roll', methods=['POST'])
def roll_dice():
    data        = request.json or {}
    player_name = data.get('player_name', '').strip()
    if not player_name:
        return jsonify({'error': 'Player name required'}), 400

    die1 = random.randint(1, 6)
    die2 = random.randint(1, 6)

    conn = get_db()
    cur  = conn.execute(
        'INSERT INTO dice_roll (player_name, die1, die2) VALUES (?, ?, ?)',
        (player_name, die1, die2)
    )
    roll_id = cur.lastrowid
    conn.commit()
    conn.close()

    return jsonify({'id': roll_id, 'player_name': player_name, 'die1': die1, 'die2': die2,
                    'total': die1 + die2, 'rolled_at': datetime.utcnow().isoformat()})


@app.route('/api/dice/latest', methods=['GET'])
def latest_roll():
    since_id = request.args.get('since_id', 0, type=int)
    conn = get_db()
    row  = conn.execute(
        'SELECT * FROM dice_roll ORDER BY id DESC LIMIT 1'
    ).fetchone()
    history = conn.execute(
        'SELECT * FROM dice_roll ORDER BY id DESC LIMIT 20'
    ).fetchall()
    conn.close()

    latest = dict(row) if row else None
    new_roll = latest and latest['id'] > since_id

    return jsonify({
        'latest':   latest,
        'new_roll': new_roll,
        'history':  [dict(r) for r in history],
    })


migrate_db()

if __name__ == '__main__':
    app.run(debug=True, port=8090)
