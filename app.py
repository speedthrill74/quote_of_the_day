from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from flask_cors import CORS

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://zrzghneqdaexkz:f50076194c4aee6cb57fd34bb69667adb1b1f17d24ab6e11c6a636e428553b6b@ec2-44-193-188-118.compute-1.amazonaws.com:5432/d3kph57kl3l8kv"

db = SQLAlchemy(app)
ma = Marshmallow(app)
bcrypt = Bcrypt(app)
CORS(app)


class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String, nullable=False)
    author = db.Column(db.String)
    
    def __init__(self, text, author):
        self.text = text
        self.author = author
        
class Date(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Integer, nullable=False)
    quote = db.Column(db.Integer, nullable=False)
    
    def __init__(self, day, quote):
        self.day = day
        self.quote = quote
        
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    
    def __init__(self, username, password):
        self.username = username
        self.password = password
        
        
class QuoteSchema(ma.Schema):
    class Meta:
        fields = ("id", "text", "author")
        
quote_schema = QuoteSchema()
multiple_quote_schema = QuoteSchema(many=True)

class DateSchema(ma.Schema):
    class Meta:
        fields = ("id", "day", "quote")
        
date_schema = DateSchema()

class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "username", "password") #TODO Remove sensitive fields
        
user_schema = UserSchema()
multiple_user_schema = UserSchema(many=True)

@app.route("/quote/add", methods=["POST"])
def add_quote():
    if request.content_type != "application/json":
        return jsonify("ERROR Data must be sent as JSON")
    
    post_data = request.get_json()
    text = post_data.get("text")
    author = post_data.get("author")
    
    record = Quote(text, author)
    db.session.add(record)
    db.session.commit()
    
    return jsonify(quote_schema.dump(record))

@app.route("/quote/get/<id>", methods=["GET"])
def get_quote_by_id(id):
    record = db.session.query(Quote).filter(Quote.id == id).first()
    return jsonify(quote_schema.dump(record))


@app.route("/date/add", methods=["POST"])
def create_initial_date():
    record_check = db.session.query(Date).first()
    if record_check is not None:
        return jsonify("ERROR: Date has already been initialized")
    
    if request.content_type != "application/json":
        return jsonify("ERROR: Data must be sent as JSON")
    
    post_data = request.get_json()
    day = post_data.get("day")
    quote = post_data.get("quote")
    
    record = Date(day, quote)
    db.session.add(record)
    db.session.commit()
    
    return jsonify(date_schema.dump(record))

@app.route("/date/get", methods=["GET"])
def get_date():
    record = db.session.query(Date).first()
    return jsonify(date_schema.dump(record))

@app.route("/date/update", methods=["PUT"])
def update_date():
    record = db.session.query(Date).first()
    if record is None:
        return jsonify("ERROR: Date has not been initialized")
    
    if request.content_type != "application/json":
        return jsonify("ERROR: Data must be sent as JSON")
    
    put_data = request.get_json()
    day = put_data.get("day")
    
    all_quotes = db.session.query(Quote).all()
    current_quote = db.session.query(Quote).filter(Quote.id == record.quote).first()
    current_quote_index = all_quotes.index(current_quote)
    if current_quote_index + 1 < len(all_quotes):
        next_quote = all_quotes[current_quote_index + 1]
    else:
        next_quote = all_quotes[0]
    
    record.day = day
    record.quote = next_quote.id
    db.session.commit()
    
    return jsonify(date_schema.dump(record))

@app.route("/user/add", methods=["POST"])
def add_user():
    if request.content_type != "application/json":
        return jsonify("ERROR: Data must be sent as JSON.")

    post_data = request.get_json()
    username = post_data.get("username")
    password = post_data.get("password")
    
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    record_check = db.session.query(User).filter(User.username == username).first()
    if record_check is not None:
        return jsonify("Error: Username already exists.")

    record = User(username, hashed_password)
    db.session.add(record)
    db.session.commit()

    return jsonify(user_schema.dump(record))

@app.route("/user/get", methods=["GET"])
def get_all_users():
    records = db.session.query(User).all()
    return jsonify(multiple_user_schema.dump(records))

@app.route("/user/login", methods=["POST"])
def login():
    if request.content_type != "application/json":
        return jsonify("ERROR: Data must be sent as JSON.")

    post_data = request.get_json()
    username = post_data.get("username")
    password = post_data.get("password")

    record = db.session.query(User).filter(User.username == username).first()
    if record is None:
        return jsonify("User NOT verified")

    if not bcrypt.check_password_hash(record.password, password):
        return jsonify("User NOT verified")

    return jsonify("User verified")
    

if __name__ == '__main__':
    app.run(debug=True)
    
