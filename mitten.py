from flask import Flask, request, Response, jsonify, redirect, render_template, session
import bcrypt
from secrets import token_urlsafe
import requests
from time import time

from pymongo import MongoClient
client = MongoClient('localhost', 27017)
db = client.mitten
users = db.users

app = Flask(__name__)

ports = {
    'B1' : 8081,
    'B2' : 8082,
    'B3' : 8083,
}

@app.route('/user', methods = ['POST'])
def create_user():
    email    = request.form.get('email')
    password = request.form.get('password').encode()
    name     = request.form.get('name')

    salt   = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)
    token  = token_urlsafe(16) 

    users.insert({
        'email'  : email,
        'hashed' : hashed,
        'name'   : name,
        'salt'   : salt,
        'token'  : token,
    })

    return 'ok'

@app.route('/user', methods = ['GET'])
def get_user():
    print(request)
    email    = request.form.get('email')
    password = request.form.get('password').encode()

    user = users.find_one({'email' : email})

    salt   = user['salt']
    hashed = bcrypt.hashpw(password, salt)

    if user['hashed'] == hashed:
        return jsonify({'token' : user['token'],
                        'name'  : user['name'],
        }) 
    else:
        return 'da-te in mortii ma-tii'

@app.route('/accounts', methods = ['GET'])
def accounts():
    email    = request.form.get('email')
    token    = request.form.get('token')

    user = users.find_one({'email' : email})

    if user['token'] == token:
        if 'accounts' in user:
            return jsonify(user['accounts'])
        else:
            return jsonify([])
    else:
        return 'da-te in mortii ma-tii'

@app.route('/transaction', methods = ['POST'])
def transaction():
    email     = request.form.get('email')
    ammount   = request.form.get('ammount')
    token     = request.form.get('token')
    accountID = request.form.get('accountID')
    accountIDdest = request.form.get('accountIDdest')
    currency  = request.form.get('currency')
    ttype     = request.form.get('type')
    timestamp = time()

    user = users.find_one({'email' : email})

    if user['token'] == token:
        r = requests.post('http://34.89.193.58:' + ports[accountIDdest[:2]] + '/add',
                data = {'accountID' : accountIDdest,
                        'ammount'   : ammount,
                       })


        users.update({'email' : email},
                      {'$push' : {'transactions' : {
                                  'accountID'     : accountID,
                                  'currency'      : currency,
                                  'accountIDdest' : accountIDdest,
                                  'type'          : ttype,
                                  'timestamp'     : timestamp,
                      }}})

        return 'ok'
    else:
        return 'da-te in mortii ma-tii'

@app.route('/account', methods = ['POST'])
def account():
    email     = request.form.get('email')
    token     = request.form.get('token')
    accountID = request.form.get('accountID')
    currency  = request.form.get('currency')

    user = users.find_one({'email' : email})

    if user['token'] == token:
        users.update({'email' : email},
                      {'$push' : {'accounts' : {
                                  'accountID' : accountID,
                                  'currency'  : currency,
                      }}})

        return 'ok'
    else:
        return 'da-te in mortii ma-tii'

@app.route('/card', methods = ['POST'])
def card():
    uid           = request.form.get('uid')
    ammount       = request.form.get('ammount')
    currency      = request.form.get('currency')
    accountIDdest = request.form.get('accountIDdest')
    ttype         = request.form.get('type')

    user = users.find_one({'card' : uid})

    print(user)

    token = user['token']

    print(token)

    for account in user['accounts']:
        print(account)
        if account['currency'] == currency:
            r = requests.post('http://34.89.193.58:8080/transaction',
                json = {'accountID' : accountIDdest,
                        'ammount'   : ammount,
                        'email'     : user['email'],
                        'token'     : token,
                        'type'      : ttype,
                        'currency'  : currency,
                       })

            return 'Transaction succesfull'
    return 'Transaction failed'

if __name__ == '__main__':
    app.run(port = 8080,
            host = '0.0.0.0',
            debug = True,
            )
