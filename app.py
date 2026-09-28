from flask import Flask, render_template, request, redirect, flash, session
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from passlib.hash import sha256_crypt
from dotenv import load_dotenv
import os
load_dotenv()
app = Flask(__name__)
app.config["MONGO_URI"] = os.getenv("MONGOURI", "mongodb://localhost:27017/flight_booking_system")
app.config["SECRET_KEY"] = os.getenv("SECRETKEY") or os.urandom(32)
mongo = PyMongo(app)
mongo.db.Flights.delete_many({})
mongo.db.Bookings.delete_many({})
@app.route('/')
def index():
    if mongo.db.Flights.count_documents({}) == 0:
        flights = [
            {"flight_number": "AA123", "departure": "New York", "arrival": "Los Angeles", "price": 200},
            {"flight_number": "BB456", "departure": "Chicago", "arrival": "Miami", "price": 150},
            {"flight_number": "CC789", "departure": "San Francisco", "arrival": "Seattle", "price": 300},
            {"flight_number": "DD101", "departure": "Boston", "arrival": "Dallas", "price": 180},
            {"flight_number": "EE202", "departure": "Atlanta", "arrival": "Denver", "price": 220},
            {"flight_number": "FF303", "departure": "Houston", "arrival": "Phoenix", "price": 250},
            {"flight_number": "GG404", "departure": "Las Vegas", "arrival": "Orlando", "price": 170},
            {"flight_number": "HH505", "departure": "Seattle", "arrival": "San Diego", "price": 190},
            {"flight_number": "II606", "departure": "Philadelphia", "arrival": "San Antonio", "price": 210},
            {"flight_number": "JJ707", "departure": "Detroit", "arrival": "Charlotte", "price": 160},
            {"flight_number": "KK808", "departure": "Portland", "arrival": "Salt Lake City", "price": 230},
            {"flight_number": "LL909", "departure": "Minneapolis", "arrival": "Tampa", "price": 240},
            {"flight_number": "MM010", "departure": "Cleveland", "arrival": "Nashville", "price": 200},
            {"flight_number": "NN111", "departure": "Kansas City", "arrival": "Indianapolis", "price": 180},
            {"flight_number": "OO212", "departure": "Austin", "arrival": "Memphis", "price": 190},
            {"flight_number": "PP313", "departure": "Denver", "arrival": "Las Vegas", "price": 220},
            {"flight_number": "QQ414", "departure": "San Jose", "arrival": "Sacramento", "price": 120},
            {"flight_number": "RR515", "departure": "Columbus", "arrival": "Cincinnati", "price": 140},
            {"flight_number": "SS616", "departure": "Milwaukee", "arrival": "St. Louis", "price": 160},
            {"flight_number": "TT717", "departure": "Baltimore", "arrival": "Richmond", "price": 130},
            {"flight_number": "UU818", "departure": "Pittsburgh", "arrival": "Buffalo", "price": 150},
            {"flight_number": "VV919", "departure": "Albuquerque", "arrival": "El Paso", "price": 170},
            {"flight_number": "WW020", "departure": "Omaha", "arrival": "Des Moines", "price": 180},
            {"flight_number": "XX121", "departure": "Raleigh", "arrival": "Charleston", "price": 200},
            {"flight_number": "YY222", "departure": "Boise", "arrival": "Spokane", "price": 190},
            {"flight_number": "ZZ323", "departure": "Anchorage", "arrival": "Fairbanks", "price": 250}
        ]
        mongo.db.Flights.insert_many(flights)
    flights = mongo.db.Flights.find()
    return render_template("index.html", flights = flights)
@app.route("/register", methods = ["GET", "POST"])
def register():
    flash(("Successfully registered an account", "success"))
    document = {}
    document["email"] = request.form.get("email")
    document["password"] = sha256_crypt.hash(request.form.get("password"))
    mongo.db.Accounts.insert_one(document)
    return redirect("/")
@app.route("/login", methods = ["GET", "POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    real_password = mongo.db.Accounts.find_one({"email": email})["password"]
    if real_password:
        if sha256_crypt.verify(password, real_password):
            session["email"] = email
            session["user_id"] = mongo.db.Bookings.insert_one({"bookings": []}).inserted_id
            flash(("Login successful", "success"))
            return redirect("/flights")
        else:
            flash(("Password is incorrect", "danger"))
            return redirect("/")
    flash(("Please register an account", "danger"))
    return redirect("/")
@app.route("/flights", methods = ["GET", "POST"])
def flights():
    if "email" not in session:
        flash(("Please login to view flights", "danger"))
        return redirect("/")
    flights = mongo.db.Flights.find()
    bookings_count = len(mongo.db.Bookings.find_one({"_id": ObjectId(session["user_id"])})["bookings"])
    return render_template("flights.html", flights = flights, email = session["email"], bookings_count = bookings_count)
@app.route("/book_flight/<flight_id>", methods = ["GET", "POST"])
def book_flight(flight_id):
    bookings = mongo.db.Bookings.find_one({"_id": ObjectId(session["user_id"])})["bookings"]
    for booking in bookings:
        if booking["flight_number"] == request.form.get("flight_number"):
            mongo.db.Bookings.update_one({"_id": ObjectId(session["user_id"]), "bookings.flight_number": request.form.get("flight_number")}, {"$set": {"bookings.$.quantity": booking["quantity"] + int(request.form.get("quantity"))}})
            flash(("Flight booked successfully", "success"))
            return redirect("/flights")
    booking = {}
    booking["flight_number"] = request.form.get("flight_number")
    booking["departure"] = request.form.get("departure")
    booking["arrival"] = request.form.get("arrival")
    booking["quantity"] = int(request.form.get("quantity"))
    booking["price"] = int(mongo.db.Flights.find_one({"_id": ObjectId(flight_id)})["price"])
    mongo.db.Bookings.update_one({"_id": ObjectId(session["user_id"])}, {"$addToSet": {"bookings": booking}})
    flash(("Flight booked successfully", "success"))
    return redirect("/flights")
@app.route("/logout")
def logout():
    session.pop("email")
    flash(("Logout successful", "success"))
    return redirect("/")
@app.route("/view_bookings", methods = ["GET", "POST"])
def view_bookings():
    bookings = list(mongo.db.Bookings.find_one({"_id": ObjectId(session["user_id"])})["bookings"])
    total = 0
    for i in bookings:
        total += (i["quantity"] * i["price"])
    return render_template("confirm_bookings.html", bookings = bookings, total = total)
@app.route("/delete_booking/<flight_number>")
def delete_booking(flight_number):
    mongo.db.Bookings.update_one({"_id": ObjectId(session["user_id"])}, {"$pull": {"bookings": {"flight_number": flight_number}}})
    return redirect("/view_bookings")
@app.route("/checkout", methods = ["GET", "POST"])
def checkout():
    session.pop("email")
    flash(("Checked out successfully", "success"))
    return redirect("/flights")
if __name__ == '__main__':
    app.run(debug = True)