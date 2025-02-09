from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
import requests

API_KEY = "1f7a5937388e21ffc2fadab68ab07010"
URL = "https://api.themoviedb.org/3/search/movie?include_adult=false&language=en-US&page=1"
PICTURE_PATH = "https://image.tmdb.org/t/p/w500"

app = Flask(__name__)
app.config["SECRET_KEY"] = "8BYkEfBA6O6donzWlSihBXox7C0sKR6b"
Bootstrap(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movie-collection.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)  # db.create_all() To first create the db


# Define the database model for storing movie information.
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


class MyRatingForm(FlaskForm):
    """Define a form class for rating and reviewing movies."""

    rating = StringField("Rating out of 10")
    review = StringField("Enter your Review")
    button = SubmitField("Update")


class MyMovieForm(FlaskForm):
    """Define a form class for adding new movies"""

    title = StringField("Movie Name")
    button = SubmitField("Enter")


@app.route("/")
def home():
    """
    Fetches all movies from the database, sorts them by rating, and updates rankings.
    Displays the list of movies on the homepage.
    """
    all_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["POST", "GET"])
def edit():
    """
    Displays a form for editing a movie's rating and review.
    Updates the movie details in the database when the form is submitted.
    """
    form = MyRatingForm()
    movie_id = request.values.get("id")
    movie = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", movie=movie, form=form)


@app.route("/delete")
def delete():
    """
    Deletes a movie from the database based on the provided movie ID.
    Redirects back to the homepage after deletion.
    """
    movie_id = request.values.get("id")
    movie_id_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_id_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["POST", "GET"])
def add():
    """
    Displays a form to search for a movie using TMDb API.
    Shows search results from the API, allowing users to select a movie to add.
    """
    form = MyMovieForm()
    if form.validate_on_submit():
        movie_title = form.title.data
        response = requests.get(URL, params={"api_key": API_KEY, "query": movie_title})
        data = response.json()["results"]
        return render_template("select.html", options=data)
    return render_template("add.html", form=form)


@app.route("/find", methods=["POST", "GET"])
def find():
    """
    Fetches detailed movie information from TMDb API based on the selected movie ID.
    Adds the movie to the database and redirects to the edit page.
    """
    movie_id = request.values.get("id")
    if movie_id:
        movie_api_url = f"https://api.themoviedb.org/3/movie/{movie_id}?language=en-US"
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIxZjdhNTkzNzM4OGUyMWZmYzJmYWRhYjY4YWIwNzAxMCIsInN1YiI6IjY0Nzc1NjM3MTJjNjA0MDExZjY2NWNhOCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.U3fma2sTbfahEQIkUp4rjpIus7H7P0ty-jE5nH7ZVXw",  # Bearer token for authorization to access the API.
        }
        response = requests.get(movie_api_url, headers=headers)
        data = response.json()
        new_movie = Movie(
            title=data["original_title"],
            year=data["release_date"].split("-")[0],
            description=data["overview"],
            rating=data["vote_average"],
            ranking="",
            review="",
            img_url=f"{PICTURE_PATH}{data['poster_path']}",
        )
        db.session.add(new_movie)
        db.session.commit()
        form = MyRatingForm()

        return render_template("edit.html", form=form, movie=new_movie)


if __name__ == "__main__":
    """Run the Flask application"""
    app.run(debug=True)
