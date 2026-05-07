"""
RedHat Airlines: Secure Ticket Purchasing System (Server-side)
CYBR 3108 | Group: Red Hat Airline
Members: Emma Austin, Carter Sloan, Brent Lewis
"""
import socket
import threading
import sqlite3
import hashlib
import uuid

HOST = "127.0.0.1"
PORT = 9999
DB_NAME = "redhat_airlines.db"
sessions = {}


# Database
# Tables:
#   - users   : stores usernames and hashed passwords
#   - flights : stores available flight listings
#   - tickets : stores ticket purchase records
#   - points  : stores each user's redeemable point balance

def create_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flights (
            flight_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            airline          TEXT NOT NULL,
            departure        TEXT NOT NULL,
            destination      TEXT NOT NULL,
            time_slot        TEXT NOT NULL,
            seat_class       TEXT NOT NULL,
            available_seats  INTEGER NOT NULL,
            price_points     INTEGER NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id            INTEGER NOT NULL,
            flight_id          INTEGER NOT NULL,
            trip_type          TEXT NOT NULL,
            baggage_option     TEXT NOT NULL,
            purchase_timestamp TEXT NOT NULL,
            FOREIGN KEY (user_id)   REFERENCES users(user_id),
            FOREIGN KEY (flight_id) REFERENCES flights(flight_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS points (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM flights")
    if cursor.fetchone()[0] == 0:
        sample_flights = [
            ("RedHat Air", "Atlanta",     "New York",    "08:00 AM", "Economy",  120, 500),
            ("RedHat Air", "Atlanta",     "Los Angeles", "10:30 AM", "Economy",   80, 750),
            ("RedHat Air", "Atlanta",     "Chicago",     "02:15 PM", "Business",  40, 900),
            ("RedHat Air", "New York",    "Atlanta",     "09:00 AM", "Economy",  100, 500),
            ("RedHat Air", "Los Angeles", "Atlanta",     "11:45 AM", "First",     20, 1200),
            ("RedHat Air", "Chicago",     "Atlanta",     "03:30 PM", "Economy",   90, 600),
        ]
        cursor.executemany(
            "INSERT INTO flights (airline, departure, destination, time_slot, "
            "seat_class, available_seats, price_points) VALUES (?,?,?,?,?,?,?)",
            sample_flights
        )

    conn.commit()
    conn.close()



# Input Validation

def hash_password(password):
    # SHA-256 one-way hash; plaintext is never stored
    return hashlib.sha256(password.encode()).hexdigest()


def valid_username(username):
    """
    Rules:
      - Not empty or None
      - At least 3 characters long
      - Contains only letters, digits, or underscores
    """
    if not username or len(username) < 3:
        return False
    for ch in username:
        if not (ch.isalnum() or ch == "_"):
            return False
    return True


def valid_password(password):
    # Minimum 8 characters, not empty
    return bool(password) and len(password) >= 8


def resolve_user_id(token):
    return sessions.get(token)


#Authentication

def register_user(username, password):
    if not valid_username(username):
        return "ERROR: Username must be 3+ characters using only letters, numbers, or underscores"

    if not valid_password(password):
        return "ERROR: Password must be at least 8 characters"

    # Hash
    password_hash = hash_password(password)

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

       
        cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return "ERROR: Username already exists"

        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        user_id = cursor.lastrowid

        # Grant 1,000 welcome points to every new account
        cursor.execute(
            "INSERT INTO points (user_id, balance) VALUES (?, ?)",
            (user_id, 1000)
        )

        conn.commit()
        conn.close()
        return "SUCCESS: Registration complete"

    except Exception:
        return "ERROR: Registration failed"


def login_user(username, password):
    if not username or not password:
        return "ERROR: Invalid username or password"

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT user_id, password_hash FROM users WHERE username = ?",
            (username,)
        )
        result = cursor.fetchone()
        conn.close()

        if result is None:
            return "ERROR: Invalid username or password"

        user_id, stored_hash = result

        # Compare hashes
        if hash_password(password) != stored_hash:
            return "ERROR: Invalid username or password"

        # Generate a cryptographically random UUID session token
        token = str(uuid.uuid4())
        sessions[token] = user_id
        return f"SUCCESS: Login complete | TOKEN: {token}"

    except Exception:
        return "ERROR: Login failed"


def login_v_user(username, password):

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

       
        query = "SELECT user_id FROM users WHERE username = '" + username + "'"
        cursor.execute(query)
        result = cursor.fetchone()
        conn.close()

        if result is None:
            return "ERROR: Invalid username or password"

       
        user_id = result[0]
        token = str(uuid.uuid4())
        sessions[token] = user_id
        return f"SUCCESS: Login complete | TOKEN: {token}"

    except Exception as e:
        return f"ERROR: Login failed - {e}"


# Flight Functions/Features

def view_flights():
    """
    Returns a list of all flights that still have available seats.
    Includes: flight ID, airline, route, departure time, seat class,
    remaining seats, and cost in points.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT flight_id, airline, departure, destination, time_slot, "
            "seat_class, available_seats, price_points "
            "FROM flights WHERE available_seats > 0"
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return "INFO: No flights currently available"

        lines = ["FLIGHTS:"]
        for row in rows:
            fid, airline, dep, dest, ts, cls, seats, pts = row
            lines.append(
                f"ID={fid} | {airline} | {dep} -> {dest} | {ts} | {cls} | Seats={seats} | Points={pts}"
            )
        return "\n".join(lines)

    except Exception:
        return "ERROR: Could not retrieve flights"


def view_flight_status(flight_id_str):
    """
    Returns the current status of a specific flight given its ID.
    Available pre-login - no authentication required.
    """
    try:
        flight_id = int(flight_id_str)
        if flight_id <= 0:
            raise ValueError()
    except ValueError:
        return "ERROR: Flight ID must be a positive integer"

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Parameterized - flight_id is user-supplied
        cursor.execute(
            "SELECT flight_id, airline, departure, destination, time_slot, "
            "seat_class, available_seats "
            "FROM flights WHERE flight_id = ?",
            (flight_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return "INFO: No flight found with that ID"

        fid, airline, dep, dest, ts, cls, seats = row

        if seats == 0:
            status = "SOLD OUT"
        elif seats <= 10:
            status = f"LIMITED ({seats} seats left)"
        else:
            status = f"AVAILABLE ({seats} seats)"

        return (
            f"FLIGHT STATUS | ID={fid} | {airline} | {dep} -> {dest} | "
            f"{ts} | {cls} | {status}"
        )

    except Exception:
        return "ERROR: Could not retrieve flight status"



def purchase_ticket(token, flight_id_str, trip_type, baggage_option):
    user_id = resolve_user_id(token)
    if user_id is None:
        return "ERROR: Not authenticated"

    try:
        flight_id = int(flight_id_str)
        if flight_id <= 0:
            raise ValueError()
    except ValueError:
        return "ERROR: Invalid flight ID"

    if trip_type.lower() not in {"one-way", "round-trip"}:
        return "ERROR: trip_type must be 'one-way' or 'round-trip'"

    if baggage_option.lower() not in {"none", "carry-on", "checked"}:
        return "ERROR: baggage_option must be 'none', 'carry-on', or 'checked'"

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT price_points, available_seats FROM flights WHERE flight_id = ?",
            (flight_id,)
        )
        flight = cursor.fetchone()
        if flight is None:
            conn.close()
            return "ERROR: Flight not found"

        price, seats = flight
        if seats <= 0:
            conn.close()
            return "ERROR: No seats available on this flight"

        total_cost = price * 2 if trip_type.lower() == "round-trip" else price

        cursor.execute("SELECT balance FROM points WHERE user_id = ?", (user_id,))
        pts_row = cursor.fetchone()
        if pts_row is None or pts_row[0] < total_cost:
            conn.close()
            return (
                f"ERROR: Insufficient points "
                f"(need {total_cost}, have {pts_row[0] if pts_row else 0})"
            )

        
        cursor.execute(
            "UPDATE points SET balance = balance - ? WHERE user_id = ?",
            (total_cost, user_id)
        )
        cursor.execute(
            "UPDATE flights SET available_seats = available_seats - 1 WHERE flight_id = ?",
            (flight_id,)
        )

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO tickets (user_id, flight_id, trip_type, baggage_option, purchase_timestamp) "
            "VALUES (?,?,?,?,?)",
            (user_id, flight_id, trip_type.lower(), baggage_option.lower(), timestamp)
        )

        conn.commit()
        conn.close()
        return (
            f"SUCCESS: Ticket purchased for flight {flight_id} | "
            f"Cost: {total_cost} points | Trip: {trip_type} | Baggage: {baggage_option}"
        )

    except Exception:
        return "ERROR: Purchase failed"


def add_points(token, amount_str):
    user_id = resolve_user_id(token)
    if user_id is None:
        return "ERROR: Not authenticated"

    try:
        amount = int(amount_str)
        if amount <= 0:
            return "ERROR: Amount must be a positive integer"
        if amount > 10000:
            return "ERROR: Maximum add per transaction is 10,000 points"
    except ValueError:
        return "ERROR: Invalid amount"

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE points SET balance = balance + ? WHERE user_id = ?",
            (amount, user_id)
        )
        cursor.execute("SELECT balance FROM points WHERE user_id = ?", (user_id,))
        new_balance = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return f"SUCCESS: {amount} points added | New balance: {new_balance}"

    except Exception:
        return "ERROR: Could not add points"


def view_points(token):
    user_id = resolve_user_id(token)
    if user_id is None:
        return "ERROR: Not authenticated"

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM points WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return f"POINTS: {row[0]}" if row else "ERROR: Could not retrieve points"
    except Exception:
        return "ERROR: Could not retrieve points"


def view_history(token):
    user_id = resolve_user_id(token)
    if user_id is None:
        return "ERROR: Not authenticated"

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.ticket_id, f.departure, f.destination, f.time_slot,
                   t.trip_type, t.baggage_option, t.purchase_timestamp
            FROM tickets t
            JOIN flights f ON t.flight_id = f.flight_id
            WHERE t.user_id = ?
            ORDER BY t.purchase_timestamp DESC
        """, (user_id,))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return "INFO: No purchase history found"

        lines = ["HISTORY:"]
        for row in rows:
            tid, dep, dest, ts, trip, bag, ts_buy = row
            lines.append(
                f"Ticket#{tid} | {dep} -> {dest} | {ts} | {trip} | "
                f"Baggage: {bag} | Purchased: {ts_buy}"
            )
        return "\n".join(lines)

    except Exception:
        return "ERROR: Could not retrieve history"


def logout_user(token):
    if token in sessions:
        del sessions[token]
        return "SUCCESS: Logged out"
    return "ERROR: Invalid session"



def handle_client(conn, addr):
    """
    Handles all commands from a single connected client on its own thread.

    Commands:
      REGISTER     <username> <password>
      LOGIN        <username> <password>
      LOGIN_VUL    <username>|<password>
      FLIGHTSTATUS <flight_id>
      FLIGHTS
      PURCHASE     <token> <flight_id> <trip_type> <baggage_option>
      ADDPOINTS    <token> <amount>
      POINTS       <token>
      HISTORY      <token>
      LOGOUT       <token>
    """
    print(f"[+] Client connected: {addr}")

    while True:
        try:
            data = conn.recv(4096).decode().strip()
            if not data:
                break

            parts = data.split()
            if not parts:
                conn.send("ERROR: Empty command".encode())
                continue

            command = parts[0].upper()

            
            if command == "REGISTER" and len(parts) == 3:
                response = register_user(parts[1], parts[2])


            elif command == "LOGIN" and len(parts) == 3:
                username = parts[1]
                password = parts[2]
                print(f"[LOGIN ATTEMPT] Username: {username} | Password: {password}")
                response = login_user(username, password)

           
            elif command == "LOGIN_VUL":
                payload = data[len("LOGIN_VUL"):].strip()
                if "|" in payload:
                    vuln_user, vuln_pass = payload.split("|", 1)
                    response = login_v_user(vuln_user, vuln_pass)
                else:
                    response = "ERROR: Usage: LOGIN_VUL <username>|<password>"

          
            elif command == "FLIGHTSTATUS" and len(parts) == 2:
                response = view_flight_status(parts[1])

            
            elif command == "FLIGHTS" and len(parts) == 1:
                response = view_flights()

            
            elif command == "PURCHASE" and len(parts) == 5:
                response = purchase_ticket(parts[1], parts[2], parts[3], parts[4])

           
            elif command == "ADDPOINTS" and len(parts) == 3:
                response = add_points(parts[1], parts[2])

           
            elif command == "POINTS" and len(parts) == 2:
                response = view_points(parts[1])

           
            elif command == "HISTORY" and len(parts) == 2:
                response = view_history(parts[1])

            
            elif command == "LOGOUT" and len(parts) == 2:
                response = logout_user(parts[1])

            else:
                response = "ERROR: Unknown or malformed command"

            conn.send(response.encode())

        except ConnectionResetError:
            break
        except Exception:
            try:
                conn.send("ERROR: Server encountered a problem".encode())
            except Exception:
                pass
            break

    conn.close()
    print(f"[-] Client disconnected: {addr}")



def start_server():
    """
    Initializes the database, creates the TCP listening socket, and enters
    the main accept loop. Each client connection is dispatched to
    handle_client() on its own daemon thread.
    """
    create_database()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[*] RedHat Airlines Server running on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        thread.start()


if __name__ == "__main__":
    start_server()
