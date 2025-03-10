from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import random
import bcrypt
import time

import os

load_dotenv()
password = os.getenv('PASSWORD')
        
url = f'mongodb+srv://samburg:{password}@samsdata.266tr.mongodb.net/?retryWrites=true&w=majority&appName=SamsData'


def store_mongo_data(data, username):
    
    # Create a new client and connect to the server
    client = MongoClient(url, server_api=ServerApi('1'))

    database = client.get_database('halloween')
    spots = database.get_collection('locations')
    
    data_to_save = {
        "username"   : username,
        "time_stamp" : data["time_stamp"],
        "lat"        : data["lat"],
        "lng"        : data["lng"],
        "iconUrl"    : data["iconUrl"]
    }

    spots.insert_one(data_to_save)
    
    client.close()


    

def retrieve_data():
    
            # Create a new client and connect to the server
    client = MongoClient(url, server_api=ServerApi('1'))

    database = client.get_database('halloween')
    spots = database.get_collection('locations')
    
    spot_data = []
    response = spots.find()
    
    for i in response:
        data = {}
        data["username"] = i["username"]
        data["time_stamp"] = i["time_stamp"]
        data["lng"] = i["lng"]
        data["lat"] = i["lat"]
        data["iconUrl"] = i["iconUrl"]
        spot_data.append(data)

    return spot_data



def remove_users_spots(username):
    
    # Create a new client and connect to the server
    client = MongoClient(url, server_api=ServerApi('1'))

    database = client.get_database('halloween')
    spots = database.get_collection('locations')
    
    spots.delete_many({"username" : username})
    client.close()
    
    
    
#####################################################
##### User Registration
#####################################################

def check_user_exsists(username):
    
    # Create a new client and connect to the server
    client = MongoClient(url, server_api=ServerApi('1'))

    database = client.get_database('halloween')
    spots = database.get_collection('Users')
    
    result = spots.find_one({"username" : username})
    
    return result


def create_user(username, email, password):
    
    # Create a new client and connect to the server
    client = MongoClient(url, server_api=ServerApi('1'))

    database = client.get_database('halloween')
    spots = database.get_collection('Users')   
    
    unhasded_password = password.encode("utf-8")
    hashed_password = bcrypt.hashpw(unhasded_password, bcrypt.gensalt())
    
    verification_code = random.randint(999, 9999)
    
    user = {
        "username" : str(username),
        "email" : str(email),
        "password" : hashed_password,
        "email_verified" : False,
        "verification_attempts" : 0,
        "verification_code" : int(verification_code),
        "total_spots" : int(0)
    }
    
    spots.insert_one(user)
    client.close()
    
    return int(verification_code)


def email_verified(username):
    
    # Create a new client and connect to the server
    client = MongoClient(url, server_api=ServerApi('1'))

    database = client.get_database('halloween')
    spots = database.get_collection('Users')
    
    spots.update_one(
        {"username" : username},
        { "$set" : { "email_verified" : True , "verification_attempts": 0 }}
    )
    client.close()
    
def email_verify_attempts(username):
    
    # Create a new client and connect to the server
    client = MongoClient(url, server_api=ServerApi('1'))

    database = client.get_database('halloween')
    spots = database.get_collection('Users')
    
    spots.update_one(
        {"username" : username},
        { "$inc" : { "verification_attempts" : 1 }}
    )
    client.close()
    
    
def delete_timed_out_registration(username):
    
    # Create a new client and connect to the server
    client = MongoClient(url, server_api=ServerApi('1'))

    database = client.get_database('halloween')
    user = database.get_collection('Users')
    
    check_verified = user.find_one({ "username" : username })
    if check_verified["email_verified"]:
        print(f"Username: {username} has verified")
        return
    else:
        user.delete_one({ "username" : username })
        print(F"Username- {username} has timed out and been deleted! ")
    client.close()
    return


def verification_timer(username):
    
    ''' Run a seperate thread to check if user verified their account in 10min
        If the user fails to varify their information will be deleted '''
    
    time_start = time.time()  
    time_end = time_start + 100  # 10 min
    print(f"Starting Timer to verifiy {username}")
    while True:
        if time.time() >= time_end:
            delete_timed_out_registration(username) # functions checks verification first
            return
        else:
            time.sleep(30)
    
#####################################################
##### User login
#####################################################

def check_user_login(hashed_password, password):
    
    unhashed_password = password.encode("utf-8")
    result = bcrypt.checkpw(unhashed_password, hashed_password)

    return result


def update_user_spots(username):
    
    # Create a new client and connect to the server
    client = MongoClient(url, server_api=ServerApi('1'))

    database = client.get_database('halloween')
    user = database.get_collection('Users')
    
    user.update_one(
        {"username" : username },
        { "$inc" : { "total_spots" : 1 }}
    )
    client.close()