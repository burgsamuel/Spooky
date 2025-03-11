from flask import Flask, render_template, request, jsonify, flash, session, redirect
import mailservice
import threading
import mongodb
import time


app = Flask(__name__)


app.secret_key = 'afsd7890%^&*akjh%BJHG*MJN'
app.config["SESSION_TYPE"] = "filesystem"

login_attemps = []

@app.get("/")
def home_page():
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



@app.get("/userspots")
def update_user_spots():
    try:
        if session["logged_in"]:
            userspots = mongodb.retrieve_user_spots(session["logged_in"])
            return ({"spots" : userspots})
    except KeyError:
        return( { "spots" : "Fail" } )


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
    
    try:
        if session["logged_in"]:
            flash("You are already logged in 🎃")
            return render_template("homepage.html", user=session["logged_in"])
    except KeyError:
        pass
        
    try:
        ip_address = request.remote_addr
    except Exception as error:
        print(error)
        ip_address = "Address Unavailable"
    login_data = {
        "ip" : ip_address,
        "attemps" : 0,
        "end_time" : 0
    }
    
    for index, item in enumerate(login_attemps):
        if item["ip"] == ip_address:
            if item["attemps"] >= 3:
                time_now = time.time()
                if time_now >= item["end_time"]:
                    login_attemps.pop(index)
                    print("LOCKOUT TIMER RELEASED!")
                    return render_template("login/loginForm.html")
                else:
                    time_left = (int(item["end_time"]) - int(time_now)) / 60
                    flash(f"Please wait: {round(time_left)}-mins before trying again!!")
                    return render_template("infopage.html", bad=True)
    
    for items in login_attemps:
        if ip_address == items["ip"]:
            return render_template("login/loginForm.html")
    login_attemps.append(login_data)
    print(*login_attemps)
    return render_template("login/loginForm.html")



@app.post("/login")
def login_request():
    username = request.form["username"]
    password = request.form["password"]
    try:
        ip_address = request.remote_addr
    except Exception as error:
        print(error)
        ip_address = "Address Unavailable"
    
    print(*login_attemps)
    for item in login_attemps:
        if item["ip"] == ip_address:
            if item["attemps"] >= 3:
                # set a timer to restrict user access 
                item["end_time"] = time.time() + 1200
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
        
        session["logged_in"] = username
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
        # print(f"Verification Code: {verification_code}")
        mail_thread = threading.Thread(target=mailservice.email_confirmation, args=(email, verification_code))
        mail_thread.start()
        session["verification_pending"] = username
        verification_code_timer = threading.Thread(target=mongodb.verification_timer, args=(username,))
        verification_code_timer.start()
        return render_template("login/emailVerify.html", email=email, user=username)


@app.post("/verificationcode")

def verify_user_email():
    
    username = session["verification_pending"]
    code = int(request.form["code"])
    
    user_data = mongodb.check_user_exsists(username)
    
    try:
        user_attemps = user_data["verification_attempts"]
    except:  # noqa: E722
        session.clear()
        flash("Time to verifiy has passed!")
        return render_template("homepage.html", bad=True)
    
    if username is not None and user_attemps < 4:
        
        emailed_code = int(user_data["verification_code"])
        # print(f"Emailed Code: {emailed_code}")
        
        if emailed_code == code:
            
            session.pop("verification_pending", default=None)
            session["logged_in"] = user_data["username"]
            verify_email = threading.Thread(target=mongodb.email_verified, args=(username,))
            verify_email.start()
            flash("Code Verified!")
            return render_template("homepage.html", user=session["logged_in"])
        
        else:
            
            mongodb.email_verify_attempts(username)
            flash("Incorrect code!")
            return render_template("login/emailVerify.html")
    else:
        
        session.clear()
        flash("You Have Entered Code Wrong Too Many Times!!")
        return render_template("homepage.html", bad=True)


########################################################
## Password Reset
########################################################

@app.get("/resetpassword")
def reset_password():
    return render_template("passwordreset/resetform.html")



@app.post("/passwordresetemail")
def reset_password_post():
    username = request.form["username"]
    email = request.form["email"]
    
    user_data = mongodb.check_user_exsists(username)
    
    if user_data is not None:
        saved_email = user_data["email"]
        if email != saved_email:
            flash("Sorry incorrect details!")
            return render_template("infopage.html", bad=True)
        else:
            # Set new verification code in DB
            verification_code = mongodb.password_reset_verification_code(username)
            send_email = threading.Thread(target=mailservice.email_password_reset, args=(saved_email, verification_code))
            send_email.start()
            # print(verification_code)
            session["email_reset"] = username
            return render_template("passwordreset/passwordresetcode.html", user=username, email=saved_email)
    
    return render_template("passwordreset/resetform.html")



@app.post("/passwordresetcode")
def verify_password_code():
    
    user_code = request.form["code"]
    try:
        username = session["email_reset"]
    except KeyError:
        return redirect("/")

    user_data = mongodb.check_user_exsists(username)
    
    try:
        user_attemps = user_data["verification_attempts"]
        end_time = user_data["end_timer"]
    except Exception as error:
        print(error)
        session.clear()
        flash("Error in password reset!")
        return render_template("infopage.html", bad=True)
    
    if username is not None and user_attemps < 4 and time.time() < end_time:
        
        emailed_code = int(user_data["verification_code"])
        # print(f"Emailed Code: {emailed_code}")
    
        if int(emailed_code) == int(user_code):
            
            reset_counters = threading.Thread(target=mongodb.password_code_verified, args=(username,))
            reset_counters.start()    
            # New Password
            flash("Code Verified!")
            return render_template("passwordreset/newpassword.html")
            
        else:
                   
            mongodb.email_verify_attempts(username)
            flash("Incorrect code!")
            return render_template("passwordreset/passwordresetcode.html")
    else:
        
        session.clear()
        if time.time() > end_time:
            flash("Reset has timed out!!")
        else:
            flash("You Have Entered Code Wrong Too Many Times!!")
        return render_template("homepage.html", bad=True)



@app.post("/updatepassword")
def store_new_password():
    
    try:
        username = session["email_reset"]
    except Exception as error:
        print(error)
        return redirect("/")

    unhased_password = request.form["password"]
    
    store_new_password = threading.Thread(target=mongodb.update_new_password, args=(username, unhased_password))
    store_new_password.start()
    session.clear()
    session["logged_in"] = username
    flash("Password Reset and logged in!")
    return render_template("homepage.html", user=session["logged_in"])
    
    
    

########################################################
## Start app
########################################################

if __name__ == "__main__":
    # app.run()
    app.run(debug=True, host="0.0.0.0")