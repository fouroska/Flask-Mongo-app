from flask import Flask, request, jsonify
import pymongo
import uuid
import json
from datetime import datetime

app = Flask(__name__)

# Σύνδεση με MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["your_database_name"]
users = db["users"]
students = db["students"]

# Route για τη δημιουργία χρήστη
@app.route('/createUser', methods=['POST'])
def create_user():
    data = request.get_json()
    user = users.find_one({"username": data["username"]})

    if user:
        return jsonify({"message": "User already exists"}), 400

    # Δημιουργία νέου χρήστη
    users.insert_one({
        "username": data["username"],
        "password": data["password"],  # Προσοχή με τα passwords - χρησιμοποίησε hash
        "email": data["email"],
        "uuid": str(uuid.uuid4())
    })

    students.insert_one({
        "email": data["email"],  # Θα χρησιμοποιήσουμε το ίδιο email
        "name": data.get("name", "Unknown"),  # Όνομα για το φοιτητή
        "age": data.get("age", 18),  # Προσθέτουμε την ηλικία για το παράδειγμα
        "courses": [],  # Ξεκινάμε χωρίς μαθήματα
        "address": None,  # Αφήνουμε την διεύθυνση κενή για το παράδειγμα
        "uuid": str(uuid.uuid4())  # Βάζουμε το ίδιο uuid για να υπάρχει σύνδεση με τον χρήστη
    })
    
    return jsonify({"message": "User created successfully"}), 201

# Route για login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = users.find_one({"username": data["username"]})

    if not user or user["password"] != data["password"]:
        return jsonify({"message": "Invalid credentials"}), 401

    return jsonify({"message": "Login successful", "uuid": user["uuid"]}), 200

# Route για την αναζήτηση φοιτητή
@app.route('/getStudent', methods=['GET'])
def get_student():
    email = request.args.get('email')
    student = students.find_one({"email": email})

    if not student:
        return jsonify({"message": "Student not found"}), 404

    student.pop('_id', None)  # Αφαίρεση του _id από την απάντηση
    return jsonify(student), 200

# Route για φοιτητές 30 ετών
@app.route('/getStudents/thirties', methods=['GET'])
def get_students_thirties():
    students_list = students.find({"age": 30})
    students_list = list(students_list)
    for student in students_list:
        student.pop('_id', None)
    return jsonify(students_list), 200

# Route για φοιτητές τουλάχιστον 30 ετών
@app.route('/getStudents/oldies', methods=['GET'])
def get_students_oldies():
    students_list = students.find({"age": {"$gte": 30}})
    students_list = list(students_list)
    for student in students_list:
        student.pop('_id', None)
    return jsonify(students_list), 200

# Route για αναζήτηση διεύθυνσης φοιτητή
@app.route('/getStudentAddressByEmail', methods=['GET'])
def get_student_address():
    email = request.args.get('email')
    student_temp = students.find_one({"email": email})

    if not student_temp:
        return jsonify({"message": "Student not found"}), 404

    # Προσθήκη έλεγχου για το πεδίο "address"
    if "address" not in student_temp or student_temp["address"] is None:
        return jsonify({"message": "Address not found"}), 404

    return jsonify({"address": student_temp["address"]}), 200

# Route για διαγραφή φοιτητή
@app.route('/deleteStudent', methods=['DELETE'])
def delete_student():
    email = request.args.get('email')
    student = students.find_one({"email": email})

    if not student:
        return jsonify({"message": "Student not found"}), 404

    students.delete_one({"email": email})
    return jsonify({"message": "Student deleted successfully"}), 200

# Route για προσθήκη μαθημάτων σε φοιτητή
@app.route('/addCourses', methods=['POST'])
def add_courses():
    data = request.get_json()
    student = students.find_one({"email": data["email"]})

    if not student:
        return jsonify({"message": "Student not found"}), 404

    # Αντικατάσταση ή προσθήκη νέων μαθημάτων
    students.update_one(
        {"email": data["email"]},
        {"$push": {"courses": {"$each": data["courses"]}}}
    )
    return jsonify({"message": "Courses added successfully"}), 200

# Route για την αρχική σελίδα
@app.route('/')
def home():
    return "Welcome to the Flask app!"

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
