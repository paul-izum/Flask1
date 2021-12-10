import os
import sqlite3
from flask import Flask, jsonify, abort, request
from sqlite3 import Error
from pathlib import Path
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

BASE_DIR = Path(__file__).parent

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace("://", "ql://", 1) \
                                        or f"sqlite:///{BASE_DIR / 'test.db'}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class AuthorModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True)
    quotes = db.relationship('QuoteModel', backref='author', lazy='dynamic')

    def __init__(self, name):
        self.name = name

    def to_dict(self):
        d = {}
        for column in self.__table__.columns:
            d[column.name] = str(getattr(self, column.name))
        return d


class QuoteModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey(AuthorModel.id))
    text = db.Column(db.String(255), unique=False)

    def __init__(self, author, text):
        self.author_id = author.id
        self.text = text

    def to_dict(self):
        d = {}
        for column in self.__table__.columns:
            d[column.name] = str(getattr(self, column.name))
        del d["author_id"]
        d["author"] = self.author.to_dict()
        return d


# AUTHORS API
@app.route("/authors", methods=["POST"])
def create_author():
    new_author = request.json
    print(new_author)
    # FIXME: обработать ошибку создания одинаковых пользователей
    author = AuthorModel(**new_author)
    db.session.add(author)
    db.session.commit()
    return jsonify(author.to_dict()), 201


@app.route("/author/<int:id>")
def get_author_by_id(id):
    author = AuthorModel.query.get(id)  # None
    if author is None:
        abort(404, f"author with id={id} not found")
    # object --> dict --> json
    return jsonify(author.to_dict())

@app.route("/author/")
def get_author_all():
    authors = AuthorModel.query.all()  # None
    authors = [author.to_dict() for author in authors]
    if authors is None:
        abort(404, f"authors not found")
    # object --> dict --> json
    return jsonify(authors)




# QUOTES API
@app.route("/quotes/<int:id>")
def get_quote_by_id(id):
    quote = QuoteModel.query.get(id)  # None
    if quote is None:
        abort(404, f"quote with id={id} not found")
    # object --> dict --> json
    return jsonify(quote.to_dict())


@app.route("/quotes")  # GET
def get_all_quotes():
    quotes = QuoteModel.query.all()
    quotes = [quote.to_dict() for quote in quotes]
    return jsonify(quotes)  # list[dict] --> Json(str)


@app.route("/authors/<int:author_id>/quotes", methods=["POST"])
def create_quote(author_id):
    author = AuthorModel.query.get(author_id)
    new_quote = request.json
    q = QuoteModel(author, new_quote["text"])
    db.session.add(q)
    db.session.commit()
    return jsonify(q.to_dict()), 201


@app.route("/quotes/<int:id>", methods=["PUT"])
def edit_quote(id):
    new_data = request.json
    q = QuoteModel.query.get(id)
    if q is None:
        abort(404, f"quote with id = {id} not found")

    # q.author = new_data.get("author") or q.author
    if new_data.get("author"):
        q.author = new_data["author"]
    if new_data.get("text"):
        q.text = new_data["text"]
    if new_data.get("rating"):
        q.rating = new_data["rating"]

    db.session.commit()
    return jsonify(q.to_dict()), 200


@app.route("/quotes/<int:id>", methods=["DELETE"])
def delete_quote(id):
    if q := QuoteModel.query.get(id):
        db.session.delete(q)
        db.session.commit()
        return f"Quote with id {id} is deleted.", 200

    abort(404, f'Quote with id={id} not found!')


@app.route("/quotes/filter")  # GET
def get_quotes_filter():
    # URL:127.0.0.1: 5000/quotes/filter?author=Alex&rate=2
    params = request.args  # получаем QUERY-параметры GET запроса
    print("params = ", params)
    return {}


if __name__ == "__main__":
    app.run(debug=True)
