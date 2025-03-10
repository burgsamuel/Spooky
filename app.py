from flask import Flask, render_template, request, jsonify, flash, session
# from datetime import timedelta
# import mailservice
import threading
import mongodb
import time


app = Flask(__name__)


app.secret_key = 'afsd7890%^&*akjh%BJHG*MJN'
app.config["SESSION_TYPE"] = "filesystem"
# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=10)
login_attemps = []

@app.get("/")
def home_page():
    # session.clear()
    try:
        if session["verification_pending"]:
            return render_template("login/emailVerify.html")
    except KeyError:
        pass
    try:
        if session["logged_in"]:
            return render_template("homepage.html", user=session["logged_in"])
    except KeyError:
        return render_template("homepage.html"
                               )

@app.get("/logout")
def logout():
    session.clear()
    flash("Logged Out Successfully.")
    return render_template("homepage.html")
    
@app.get("/location")
def add_location():
    
    return render_template("addLocation.html")

@app.get("/mapView")
def map_view():
    return render_template("mapview.html")


@app.get("/mapData")
def collect_map_data():
    data = mongodb.retrieve_data()
    return jsonify(data)


@app.post("/locationData")
def recieve_location():
    try:
        if session["logged_in"]:
            data = request.get_json()
            mongodb.store_mongo_data(data, session["logged_in"])
            increament_user_spots = threading.Thread(target=mongodb.update_user_spots, args=(session["logged_in"],))
            increament_user_spots.start()
            return {"Status": "Recieved location and Saved ✅"}
    except KeyError:
        return {"Failed": True}


@app.post("/RemoveUserSpots")
def remove_spots():
    try:
        if session["logged_in"]:
            data = request.get_json()
            print(data)
            res = mongodb.remove_users_spots(session['logged_in'])
            return {"TotalSpots": res,
                "Success": "Spots Removed from data base"}
    except KeyError:
        return {"TotalSpots": 0,
                "Fail": "Login or Register!"}
    
    
########################################################
## Login End Points
########################################################



@app.get("/loginForm")
def login_form():
    ip_address = request.remote_addr
    login_data = {
        "ip" : ip_address,
        "attemps" : 0,
        "end_time" : 0
    }
    
    for index, item in enumerate(login_attemps):
        if item["ip"] == ip_address:
            if item["attemps"] >= 3:
                if time.time() >= item["end_time"]:
                    login_attemps.pop(index)
                    print("LOCKOUT TIMER RELEASED!")
                    return render_template("login/loginForm.html")
                else:
                    flash("Too many failed attempts!!!")
                    return render_template("infopage.html", bad=True)
    
    for items in login_attemps:
        if ip_address == items["ip"]:
            print("user in list")
            return render_template("login/loginForm.html")
    login_attemps.append(login_data)
    print(*login_attemps)
    return render_template("login/loginForm.html")



@app.post("/login")
def login_request():
    username = request.form["username"]
    password = request.form["password"]
    ip_address = request.remote_addr
    
    print(*login_attemps)
    for item in login_attemps:
        if item["ip"] == ip_address:
            if item["attemps"] >= 3:
                item["end_time"] = time.time() + 10
                print("Login Time Set")
                print(*login_attemps)
                flash("Too many failed attempts!!!")
                return render_template("infopage.html", bad=True)
    
    if len(password) <= 7:
        for item in login_attemps:
            if item["ip"] == ip_address:
                item["attemps"] += 1
        flash("Incorrect Password!")
        return render_template("login/loginForm.html") 
    
    user_data = mongodb.check_user_exsists(username)
    
    if user_data is not None:
        hashed_password = user_data["password"]
        result = mongodb.check_user_login(hashed_password, password)
    else:
        flash("User Details Not Found!")
        return render_template("login/loginForm.html")    
    if result:
        for index, item in enumerate(login_attemps):
            if item["ip"] == ip_address:
                login_attemps.pop(index)
        return render_template("homepage.html", user=username)
    else:
        for item in login_attemps:
            if item["ip"] == ip_address:
                item["attemps"] += 1
        print(*login_attemps)
        flash("Incorrect Password!")
        return render_template("login/loginForm.html")    



def start_timer():
    start = time.time()
    end = start + 20
    print("start timer")
    while True:
        if time.time() >= end:
            print("End time")
            return True
        else:
            time.sleep(5)



########################################################
## Registration
########################################################

@app.get("/registrationForm")
def registration_form():
    return render_template("login/register.html")


@app.post("/registration")
def registration_post():
    
    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]  
    
    # Check if User already exsists
    user = mongodb.check_user_exsists(username)
    if user is not None:
        flash("Username Already Taken!")
        return render_template("login/register.html")
    else:
        verification_code = mongodb.create_user(username, email, password)
        print(f"Verification Code: {verification_code}")
        # mail_thread = threading.Thread(target=mailservice.email_confirmation, args=(email, verification_code))
        # mail_thread.start()
        session["verification_pending"] = username
        verification_code_timer = threading.Thread(target=mongodb.verification_timer, args=(username,))
        verification_code_timer.start()
        return render_template("login/emailVerify.html", email=email, user=username)


@app.post("/verificationcode")

def verify_user_email():
    
    username = session["verification_pending"]
    code = int(request.form["code"])
    print(f"Enter Code: {code}")
    
    user_data = mongodb.check_user_exsists(username)
    
    try:
        user_attemps = user_data["verification_attempts"]
    except:  # noqa: E722
        session.clear()
        flash("Time to verifiy has passed!")
        return render_template("homepage.html", bad=True)
    
    if username is not None and user_attemps < 4:
        
        emailed_code = int(user_data["verification_code"])
        print(f"Emailed Code: {emailed_code}")
        
        if emailed_code == code:
            
            session.pop("verification_pending", default=None)
            session["logged_in"] = user_data["username"]
            mongodb.email_verified(username)
            return render_template("homepage.html")
        
        else:
            
            mongodb.email_verify_attempts(username)
            flash("Incorrect code!")
            return render_template("login/emailVerify.html")
    else:
        
        session.clear()
        flash("You Have Entered Code Wrong Too Many Times!!")
        return render_template("homepage.html", bad=True)







if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")