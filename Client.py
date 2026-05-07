"""
RedHat Airlines - Secure Ticket Purchasing System (Client-side)
CYBR 3108 | Group: Red Hat Airline
Members: Emma Austin, Carter Sloan, Brent Lewis
"""
import socket
import re

HOST = "127.0.0.1"
PORT = 9999


def send_request(message):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall(message.encode())
            response = s.recv(4096).decode()
            return response
    except ConnectionRefusedError:
        return "ERROR: Could not connect to server. Is the server running?"
    except Exception as e:
        return f"ERROR: {e}"


# Input Validation
def valid_username(username):
    if not username:
        return False, "Username cannot be empty"
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    if not re.match(r"^[A-Za-z0-9_]+$", username):
        return False, "Username can only contain letters, numbers, and underscores"
    return True, ""


# Password validation
def valid_password(password):
    if not password:
        return False, "Password cannot be empty"
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    return True, ""


# Input sanitization
def sanitize_input(value):
    value = value.strip()
    if "\x00" in value or "\n" in value or "\r" in value:
        return None, "Input contains invalid characters"
    return value, ""


# Pre-login Features / Functions
def check_flight_status():
    print("\n--- View Flight Status ---")
    flight_id = input("Enter Flight ID: ").strip()

    # Client-side check: must be a positive integer
    if not flight_id.isdigit() or int(flight_id) <= 0:
        print("Error: Flight ID must be a positive integer")
        return

    response = send_request(f"FLIGHTSTATUS {flight_id}")
    print(f"\nServer: {response}")


def register():
    print("\n--- Create Account ---")
    username = input("Enter username: ").strip()
    password = input("Enter password: ").strip()

    ok, msg = valid_username(username)
    if not ok:
        print(f"Error: {msg}")
        return

    ok, msg = valid_password(password)
    if not ok:
        print(f"Error: {msg}")
        return

    response = send_request(f"REGISTER {username} {password}")
    print(f"Server: {response}")


def login():
    print("\n--- Login ---")
    username = input("Enter username: ").strip()
    password = input("Enter password: ").strip()

    # Sanitize input 
    username, err = sanitize_input(username)
    if err:
        print(f"Error: {err}")
        return

    password, err = sanitize_input(password)
    if err:
        print(f"Error: {err}")
        return

    if not username or not password:
        print("Error: Username and password cannot be empty")
        return

    response = send_request(f"LOGIN {username} {password}")
    print(f"Server: {response}")

    if response.startswith("SUCCESS"):
        try:
            token = response.split("TOKEN:")[-1].strip()
            dashboard(username, token)
        except Exception:
            print("Error: Could not parse session token")



def login_v():
    print("\n--- Login (Alternative) ---")
    username = input("Enter username: ")
    password = input("Enter password: ")

    response = send_request(f"LOGIN_VUL {username}|{password}")
    print(f"Server: {response}")

    if response.startswith("SUCCESS"):
        try:
            token = response.split("TOKEN:")[-1].strip()
            dashboard("[injected user]", token)
        except Exception:
            print("Error: Could not parse session token")


# Post-Login Features/Functions
def view_flights_menu():
    response = send_request("FLIGHTS")
    print()
    for line in response.split("\n"):
        print(line)


def purchase_ticket_menu(token):
    print("\n--- Purchase Ticket ---")
    view_flights_menu()

    flight_id = input("\nEnter Flight ID to purchase: ").strip()
    if not flight_id.isdigit() or int(flight_id) <= 0:
        print("Error: Flight ID must be a positive integer")
        return

    print("Trip type options: one-way, round-trip")
    trip_type = input("Enter trip type: ").strip().lower()
    if trip_type not in {"one-way", "round-trip"}:
        print("Error: Trip type must be 'one-way' or 'round-trip'")
        return

    print("Baggage options: none, carry-on, checked")
    baggage = input("Enter baggage option: ").strip().lower()
    if baggage not in {"none", "carry-on", "checked"}:
        print("Error: Baggage option must be 'none', 'carry-on', or 'checked'")
        return

    response = send_request(f"PURCHASE {token} {flight_id} {trip_type} {baggage}")
    print(f"Server: {response}")


def add_points_menu(token):
    print("\n--- Add Points ---")
    amount = input("Enter amount of points to add (1-10000): ").strip()

    if not amount.isdigit() or int(amount) <= 0:
        print("Error: Amount must be a positive integer")
        return

    if int(amount) > 10000:
        print("Error: Maximum add per transaction is 10,000 points")
        return

    response = send_request(f"ADDPOINTS {token} {amount}")
    print(f"Server: {response}")


def view_points_menu(token):
    response = send_request(f"POINTS {token}")
    print(f"\nServer: {response}")


def view_history_menu(token):
    response = send_request(f"HISTORY {token}")
    print()
    for line in response.split("\n"):
        print(line)


# Post-Login Menu - All features require a session token to validate each request.
def dashboard(username, token):
    while True:
        print(f"\n=== RedHat Airlines Dashboard ({username}) ===")
        print("1. View Available Flights")
        print("2. Purchase Ticket")
        print("3. View My Points")
        print("4. Add Points")
        print("5. View Purchase History")
        print("6. Logout")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            view_flights_menu()
        elif choice == "2":
            purchase_ticket_menu(token)
        elif choice == "3":
            view_points_menu(token)
        elif choice == "4":
            add_points_menu(token)
        elif choice == "5":
            view_history_menu(token)
        elif choice == "6":
            response = send_request(f"LOGOUT {token}")
            print(f"Server: {response}")
            break
        else:
            print("Invalid option. Please choose 1-6.")


# Main Menu (Pre-login)
def main():
    while True:
        print("\n=== RedHat Airlines Reservation System ===")
        print("1. Create Account")
        print("2. Login")
        print("3. View Flight Status")
        print("4. Login (Alternative)")
        print("5. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            register()
        elif choice == "2":
            login()
        elif choice == "3":
            check_flight_status()
        elif choice == "4":
            login_v()
        elif choice == "5":
            print("Goodbye.")
            break
        else:
            print("Invalid choice. Please choose 1-5.")


if __name__ == "__main__":
    main()
