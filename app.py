from flask import Flask, render_template, request
import mysql.connector
from intra import register_intra_routes


app = Flask(__name__)



# Set the secret key for the Flask application
app.secret_key = 'RecipeHub'

# Database configuration
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="RecipeHub"
)

# Create a cursor to interact with the database
cursor = db.cursor()
register_intra_routes(app,cursor,db)

@app.route("/")
def home_form():
    return render_template("index.html")

@app.route("/reservation")
def reservation_form():
    return render_template("reservation.html")


@app.route("/signin")
def signin_form():
    return render_template("forms/registration.html")

@app.route("/register", methods=["POST"])
def register():
    # Retrieve form data
    username = request.form["username"]
    password = request.form["password"]
    email = request.form["email"]

    # Check if the username is already taken
    query = "SELECT * FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    if cursor.fetchone():
        return "Username already exists. Please choose a different username."

    # Insert new user into the database
    query = "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)"
    cursor.execute(query, (username, password, email))
    db.commit()

    return "User registered successfully!"





@app.route("/contact", methods=["POST"])
def contact():
    # Retrieve form data
    name = request.form["name"]
    email = request.form["email"]
    message = request.form["message"]

    # Insert the message into the database
    query = "INSERT INTO messages (name, email, message) VALUES (%s, %s, %s)"
    cursor.execute(query, (name, email, message))
    db.commit()

    # Create the success message
    message_display = f"Thank you, {name}! Your message has been sent successfully."

    # Return the success message as a simple string
    return message_display


@app.route("/reservation", methods=["POST"])
def reservation():
    # Retrieve form data
    full_name = request.form["booking-form-name"]
    phone_number = request.form["booking-form-phone"]
    reservation_time = request.form["booking-form-time"]
    reservation_date = request.form["booking-form-date"]
    number_of_people = request.form["booking-form-number"]
    comment = request.form.get("booking-form-message", "")

    # Insert the reservation into the database
    query = "INSERT INTO reservations (full_name, phone_number, reservation_time, reservation_date, number_of_people, comment) VALUES (%s, %s, %s, %s, %s, %s)"
    cursor.execute(query, (full_name, phone_number, reservation_time, reservation_date, number_of_people, comment))
    db.commit()

    # Create the success message
    message_display = f"Reservation for {full_name} has been successfully submitted!"

    # Return the success message as a simple string
    return message_display

@app.route('/intra')
def intra():
    return render_template('home.html')


if __name__ == "__main__":
    app.debug = True
    app.run()