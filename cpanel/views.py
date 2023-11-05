from django.shortcuts import render, redirect
from django.contrib import auth
import pyrebase
from django.contrib.auth import logout
import requests
import numpy as np

config = {
    "apiKey": "AIzaSyDoYIMA5UKw6nPpoMiAI7ggtYZ5O37Mrsk",
    "authDomain": "nutri-vision.firebaseapp.com",
    "databaseURL": "https://nutri-vision-default-rtdb.asia-southeast1.firebasedatabase.app",
    "projectId": "nutri-vision",
    "storageBucket": "nutri-vision.appspot.com",
    "messagingSenderId": "852048295193",
    "appId": "1:852048295193:web:440941bd658a175b3b4188",
    "measurementId": "G-5QTY9FF24S",
}

firebase = pyrebase.initialize_app(config)

database = firebase.database()
auth = firebase.auth()
global local_id


def signIn(request):
    return render(request, "signIn.html")


global name


def postSignIn(request):
    global local_id

    email = request.POST.get("email")
    passw = request.POST.get("pass")

    try:
        user = auth.sign_in_with_email_and_password(email, passw)
        idtoken = user["idToken"]

        # Get the user's email verification status
        user_info = auth.get_account_info(idtoken)
        email_verified = user_info["users"][0]["emailVerified"]

        if not email_verified:
            message = (
                "Email not verified. Please check your inbox and verify your email."
            )
            return render(request, "signIn.html", {"messg": message})

        # Access the localId
        local_id = user_info["users"][0]["localId"]
        msg = "Login Successful!"
        # You can use the 'local_id' to access the Firebase Realtime Database
        return welcomeLoader(request, msg)
    except Exception as e:
        message = "Invalid credentials: " + str(e)
        return render(request, "signIn.html", {"messg": message})


def welcomeLoader(request, msg):
    db = firebase.database()
    global name
    name = db.child("users").child(local_id).child("details").child("name").get().val()
    user_path = f"users/{local_id}/details/status"
    db.child(user_path).set("1")
    user_data_path = f"users/{local_id}"
    caloriedata = db.child(user_data_path + "/calorieData").get().val()
    bmidata = db.child(user_data_path + "/bmiData").get().val()
    calorie_data = [
        {"date": key, "calorie": value} for key, value in caloriedata.items()
    ]
    bmi_data = [{"date": key, "calorie": value} for key, value in bmidata.items()]
    return render(
        request,
        "welcome.html",
        {
            "email": name,
            "user": local_id,
            "bmiData": bmi_data,
            "calorieData": calorie_data,
            "mssg": msg,
        },
    )


def logout(request):
    auth.current_user = None
    db = firebase.database()
    user_path = f"users/{local_id}/details/status"

    db.child(user_path).set("0")

    return render(request, "signIn.html")


def signUp(request):
    return render(request, "signUp.html")


def postSignUp(request):
    name = request.POST.get("name")
    email = request.POST.get("email")
    passw = request.POST.get("pass")
    try:
        user = auth.create_user_with_email_and_password(email, passw)
        auth.send_email_verification(user["idToken"])
    except Exception as e:
        message = "Unable to create account. Try again: " + str(e)
        return render(request, "signUp.html", {"messg": message})

    uid = user["localId"]

    data = {"name": name, "status": "1"}
    mssg = "A verification email has been sent to your email address. Please check your inbox and verify your email before signing in."
    database.child("users").child(uid).child("details").set(data)
    return render(request, "signIn.html", {"messg": mssg})


# ----------------------- Authentication ENDS ---------------------------


def create(request):
    return render(request, "create.html")


from django.shortcuts import render
from django.contrib.auth import get_user


def post_create(request):
    import datetime
    from datetime import datetime

    global local_id

    if request.method == "POST":
        heightcm = float(request.POST["height"])
        weight = float(request.POST["weight"])
        heightm = heightcm / 100
        hsquare = heightm * heightm
        bmx = weight / hsquare
        bmi = round(bmx, 2)

        if bmi < 18.5:
            category = "Underweight"
            color = "#EBCF29"
        elif 18.5 <= bmi < 24.9:
            category = "Normal Weight"
            color = "#0BA350"
        elif 25 <= bmi < 29.9:
            category = "Overweight"
            color = "#F18D1D"
        else:
            category = "Obese"
            color = "#EA1D2C"

        current_date = datetime.now().strftime("%Y-%m-%d")
        db = firebase.database()
        bmi_data_path = f"users/{local_id}/bmiData/{current_date}"

        # Retrieve the existing calorie data for the current date

        # Update the database with the updated data
        db.child(bmi_data_path).set(bmi)

    return render(
        request, "report.html", {"bmi": bmi, "category": category, "color": color}
    )


def check(request):
    import time
    import datetime
    from datetime import timezone

    idtoken = request.session["uid"]
    a = auth.get_account_info(idtoken)
    a = a["users"]
    a = a[0]
    a = a["localId"]
    timeStamps = database.child("users").child(a).child("reports").shallow().get().val()
    lis_time = []

    for time in timeStamps:
        lis_time.append(time)

    lis_time.sort(reverse=True)

    work = []

    for time in lis_time:
        work.append(
            database.child("users")
            .child(a)
            .child("reports")
            .child(time)
            .child("work")
            .get()
            .val()
        )

    date = []
    for i in lis_time:
        i = float(i)
        dat = datetime.datetime.fromtimestamp(i).strftime("%H:%M %d-%m-%Y")
        date.append(dat)

    comb_lis = zip(lis_time, date, work)

    name = database.child("users").child(a).child("details").child("name").get().val()
    return render(request, "check.html", {"comb_lis": comb_lis, "email": name})


def post_check(request):
    import datetime

    time = request.GET.get("z")
    idtoken = request.session["uid"]
    a = auth.get_account_info(idtoken)
    a = a["users"]
    a = a[0]
    a = a["localId"]

    work = (
        database.child("users")
        .child(a)
        .child("reports")
        .child(time)
        .child("work")
        .get()
        .val()
    )
    progress = (
        database.child("users")
        .child(a)
        .child("reports")
        .child(time)
        .child("progress")
        .get()
        .val()
    )
    img_url = (
        database.child("users")
        .child(a)
        .child("reports")
        .child(time)
        .child("url")
        .get()
        .val()
    )

    i = float(time)
    dat = datetime.datetime.fromtimestamp(i).strftime("%H:%M %d-%m-%Y")

    name = database.child("users").child(a).child("details").child("name").get().val()
    return render(
        request,
        "post_check.html",
        {"w": work, "p": progress, "d": dat, "email": name, "i": img_url},
    )


def calorie(request):
    return render(request, "calorie.html")


def post_calorie(request):
    global local_id
    from datetime import datetime

    if request.method == "POST":
        calorie = int(request.POST["calorie"])

        # Get the current date in 'YYYY-MM-DD' format
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Access the Realtime Database
        db = firebase.database()

        # Construct the path to store calorie data for the current date
        calorie_data_path = f"users/{local_id}/calorieData/{current_date}"

        # Retrieve the existing calorie data for the current date
        existing_calorie_data = db.child(calorie_data_path).get().val()

        if existing_calorie_data is None:
            existing_calorie_data = 0  # Initialize to 0 if no existing data

        # Add the new calorie value to the existing data
        updated_calorie_data = existing_calorie_data + calorie

        # Update the database with the updated data
        db.child(calorie_data_path).set(updated_calorie_data)
        msg = "Calorie Data Added Successfully!"
        return welcomeLoader(request, msg)


# CV PART

from django.shortcuts import render
import requests
import numpy as np
from django.conf import settings
from django.core.files.storage import default_storage
from django.shortcuts import render
import cv2

import os
import tensorflow as tf
from tensorflow.keras.preprocessing import image


# Load your trained Keras model
model = tf.keras.models.load_model(
    "C:\\Users\\Kiruthik Kumar R\\Desktop\\Nutrivision\\models\\keras_model.h5"
)

# Load the class labels
with open("C:\\Users\\Kiruthik Kumar R\\Desktop\\Nutrivision\\models\\labels.txt") as f:
    labels = f.readlines()
labels = [label.strip() for label in labels]

# LjqICxAj8wr3a8RPBH+IGw==YtNllXJBlMl4AiZS
# LjqICxAj8wr3a8RPBH+IGw==YVqe9beI62vYp996
# Create your views here.


# Function to classify an image
def classify_image(file_url):
    img = image.load_img(file_url, target_size=(224, 224))
    img = image.img_to_array(img)
    img = np.expand_dims(img, axis=0)
    img = img / 255.0  # Normalize

    prediction = model.predict(img)
    class_index = np.argmax(prediction)
    return labels[class_index]


def scanner(request):
    import json
    import requests

    if request.method == "POST":
        cap = cv2.VideoCapture(0)

        # Read a frame from the webcam
        ret, frame = cap.read()

        # Define a file name for the captured image
        file_name = "static/captured_image.jpg"

        # Save the frame as an image
        cv2.imwrite(file_name, frame)

        # Release the webcam
        cap.release()

        # Classify the captured image
        Label = classify_image(file_name)

        api_url = "https://api.calorieninjas.com/v1/nutrition?query="
        api_request = requests.get(
            api_url + Label,
            headers={"X-Api-Key": "LjqICxAj8wr3a8RPBH+IGw==YVqe9beI62vYp996"},
        )
        try:
            api = json.loads(api_request.content)
            print(api_request.content)
        except Exception as e:
            api = "Oops! there was an error"
            print(e)
        return render(request, "home.html", {"api": api})
    else:
        return render(request, "home.html", {"query": "Enter a valid query"})


def addCal(request):
    import datetime
    from datetime import datetime

    global local_id

    calorie = float(request.POST["calorie"])
    count = int(request.POST["count"])
    totalCalorie = count * calorie
    calo = round(totalCalorie, 2)

    msg = dbcalAdd(calo)
    return welcomeLoader(request, msg)


def dbcalAdd(cals):
    global local_id
    from datetime import datetime

    current_date = datetime.now().strftime("%Y-%m-%d")
    # Access the Realtime Database
    db = firebase.database()
    # Construct the path to store calorie data for the current date
    calorie_data_path = f"users/{local_id}/calorieData/{current_date}"
    # Retrieve the existing calorie data for the current date
    existing_calorie_data = db.child(calorie_data_path).get().val()
    if existing_calorie_data is None:
        existing_calorie_data = 0

    updated_calorie_data = existing_calorie_data + cals
    # Update the database with the updated data
    db.child(calorie_data_path).set(updated_calorie_data)
    return "Calorie Data Added Successfully!"
