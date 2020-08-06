from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import spacy

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")

db = client.SimilarityDB
users = db["Users"]

def UserExist(username):
    if users.find({"Username":username}).count() == 0:
        return False
    else:
        return True

class Register(Resource):
    def post(self):
        posted_data = request.get_json()
        username = posted_data["username"]
        password = posted_data["password"]
        if UserExist(username):
            retJSON = {
                "status": 301,
                "message": "Invalid Username"
            }
            return jsonify(retJSON)
        hashed_pw = bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt())
        users.insert({
            "Username": username,
            "Password": hashed_pw,
            "Tokens": 6
        })
        retJSON = {
            "status": 200,
            "message": "You've successfully signed up for the API"
        }
        return jsonify(retJSON)

def verifyPw(username, password):
    if not UserExist(username):
        return False
    
    hashed_pw = users.find({
        "Username": username
    })[0]["Password"]
    if bcrypt.hashpw(password.encode("utf8"), hashed_pw) == hash:
        return True
    else:
        return False

def countTokens(username):
    tokens = users.find({
        "Username": username
    })[0]["Tokens"]
    return tokens

class Detect(Resource):
    def post(self):
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["password"]
        text1 = postedData["text1"]
        text2 = postedData["text2"]
        if not UserExist(username):
            retJSON = {
                "status": 301,
                "message": "Invalid Username"
            }
            return jsonify(retJSON)
        correct_pw = verifyPw(username, password)
        if not correct_pw:
            retJSON = {
                "status": 302,
                "message": "Invalid Password"
            }
        num_tokens = countTokens(username)
        if num_tokens <= 0:
            retJSON = {
                "status": 303,
                "message": "You're out of tokens, please refill"
            }
            return jsonify(retJSON)

        nlp = spacy.load('en_core_web_sm')
        text1 = nlp(text1)
        text2 = nlp(text2)
        ratio = text1.similarity(text2)
        retJSON = {
            "status": 200,
            "Similarity": ratio,
            "message": "Similarity score calculated successfully"
        }
        current_tokens = countTokens(username)
        users.update({
            "Username": username,
        },{
            "$set":{
                "Tokens":current_tokens-1
            }
        })
        return jsonify(retJSON)

class Refill(Resource):
    def post(self):
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["admin_pw"]
        refill_amount = postedData["refill"]
        if not UserExist(username):
            retJSON = {
                "status": 301,
                "message": "Invalid Username"
            }
            return jsonify(retJSON)
        correct_pw = "@dminP@$$w0rd"
        if not password == correct_pw:
            retJSON = {
                "status": 304,
                "message": "Invalid Admin Password"
            }
        current_tokens = countTokens(username)
        users.update({
            "Username": username
        }, {
            "$set":{
                "Tokens": refill_amount + current_tokens
            }
        })
        retJSON = {
            "status": 200,
            "message": "Refill Successful"
        }
        return jsonify(retJSON)

api.add_resource(Register, "/register")
api.add_resource(Detect, "/detect")
api.add_resource(Refill, "/refill")

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port='8080')