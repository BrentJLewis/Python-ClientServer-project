RedHat Airlines – Secure Ticket Purchasing System
Overview

RedHat Airlines is a Python-based client/server airline reservation system developed for the CYBR 3108 final project. The application simulates a secure airline ticket purchasing platform using TCP socket communication, multithreading, session authentication, and an SQLite database backend.

The project was designed to demonstrate both secure coding practices and common cybersecurity vulnerabilities. While most of the application follows secure development principles, two intentional vulnerabilities were left in the system for educational and testing purposes.

Team Members
Emma Austin
Carter Sloan
Brent Lewis
Technologies Used
Python 3
SQLite3
TCP Sockets
Multithreading
SHA-256 Password Hashing
UUID Session Tokens
Regular Expressions
System Architecture
Server

The server:

Handles multiple clients using threads
Manages authentication and session tokens
Processes flight and ticket operations
Stores all persistent data in SQLite
Client

The client:

Provides a command-line interface
Validates and sanitizes user input
Sends requests to the server
Displays responses and menus to users
Features
User Authentication
Account registration
Secure password hashing with SHA-256
UUID-based session tokens
Login/logout functionality
Username and password validation
Flight System
View available flights
Check flight status before login
Track available seat counts
Support for multiple seat classes
Ticket Purchasing
Purchase one-way or round-trip tickets
Choose baggage options
Automatic seat reduction after purchase
Purchase history tracking
Rewards Points System
1,000 welcome points for new users
Add reward points
View account balance
Spend points on flights
Database Tables
Table	Description
users	Stores usernames and hashed passwords
flights	Stores flight listings and seat availability
tickets	Stores ticket purchase records
points	Stores user point balances
Security Features

The project implements several secure programming techniques:

Password hashing using SHA-256
Parameterized SQL queries
Input validation and sanitization
Session-based authentication
Restricted username formatting
Positive integer validation
Thread-safe client handling
Intentional Vulnerabilities

This project intentionally includes two vulnerabilities for cybersecurity education and demonstration purposes.

1. SQL Injection Vulnerability

The LOGIN_VUL function directly concatenates user input into an SQL query instead of using parameterized statements.

Vulnerable code:

query = "SELECT user_id FROM users WHERE username = '" + username + "'"

This allows attackers to manipulate the SQL query and bypass authentication.

2. Credential Exposure Through Logging

During login attempts, the server prints usernames and passwords directly to the console.

Example:

print(f"[LOGIN ATTEMPT] Username: {username} | Password: {password}")

This demonstrates insecure logging practices and the risks of exposing sensitive user credentials.

Input Validation
Username Requirements
Minimum 3 characters
Letters, numbers, and underscores only
Password Requirements
Minimum 8 characters
Sanitization

The client removes potentially dangerous characters such as:

Null bytes
Newline characters
Carriage returns
Running the Project
Start the Server
python server.py
Start the Client
python client.py

The server runs locally on:

127.0.0.1:9999
Available Features
Pre-Login
Create Account
Login
View Flight Status
Alternative Login (vulnerable)
Exit
Post-Login
View Flights
Purchase Ticket
View Points
Add Points
View Purchase History
Logout
Educational Purpose

This project was created to help demonstrate:

Secure client/server application design
Authentication systems
Database interaction
Input validation
Session management
Common web and database vulnerabilities

The intentional vulnerabilities are included strictly for academic learning and security testing within a controlled environment.

Disclaimer

This project is intended for educational purposes only. The intentionally vulnerable components should not be used in production environments.