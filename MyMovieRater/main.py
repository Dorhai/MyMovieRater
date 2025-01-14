from flask import Flask, render_template, redirect, url_for, request # Flask is used for web application creation
from flask_bootstrap import Bootstrap # Flask-Bootstrap adds styling
from flask_sqlalchemy import SQLAlchemy # Flask-SQLAlchemy is an ORM for database interactions
from flask_wtf import FlaskForm # Flask-WTF facilitates web forms
from wtforms import StringField, SubmitField, HiddenField # WTForms provides form fields and validators
from wtforms.validators import DataRequired
import requests

# API_KEY and URLs used for interacting with The Movie Database (TMDb) API.
API_KEY = "1f7a5937388e21ffc2fadab68ab07010"
URL = "https://api.themoviedb.org/3/search/movie?include_adult=false&language=en-US&page=1"
PICTURE_PATH = "https://image.tmdb.org/t/p/w500" #

# Initialize Flask app, configure secret key for session and forms, and initialize extensions.
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movie-collection.db" # Path to the SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Disable SQLAlchemy tracking notifications for performance.
db = SQLAlchemy(app)
# db.create_all() To first create the db

# Define the database model for storing movie information.
class Movie(db.Model):
    # Columns define the structure of the database table.
    id = db.Column(db.Integer, primary_key=True, autoincrement=True) # DB Unique ID
    title = db.Column(db.String(250), unique=True, nullable=False) # Movie title
    year = db.Column(db.Integer, nullable=False) # Release year
    description = db.Column(db.String(500), nullable=False) # Movie description
    rating = db.Column(db.Float, nullable=True) # Movie rating
    ranking = db.Column(db.Integer, nullable=True) # Ranking of the movie
    review = db.Column(db.String(250), nullable=True) # User's review
    img_url = db.Column(db.String(250), nullable=False) # URL to the movie poster image
    
# Define a form class for rating and reviewing movies.    
class MyRatingForm(FlaskForm):
    rating = StringField('Rating out of 10') # Input field for rating
    review = StringField('Enter your Review') # Input field for review
    button = SubmitField('Update')# Submit button for the form
    
# Define a form class for adding new movies.    
class MyMovieForm(FlaskForm):
    title = StringField('Movie Name') # Input field for the movie name
    button = SubmitField('Enter') # Submit for the form

# Define the home route, displaying all movies ordered by their rating
@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all() # Fetch all movies sorted by rating
    # Update movie rankings based on their order
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit() # Save the updated rankings to the db
    return render_template("index.html", movies=all_movies) # Render the homepage with the list of movies.

# Define the edit route for updating a movie's rating and review.
@app.route("/edit", methods=['POST','GET'])
def edit():
    form = MyRatingForm()
    movie_id = request.values.get("id") # Get the movie ID from the request.
    movie = Movie.query.get(movie_id) # Fetch the movie details from the database.
    if form.validate_on_submit(): # Process the form when submitted.
        movie.rating = float(form.rating.data) # Retrieve the rating from the form.
        movie.review = form.review.data # Retrieve the review from the form.
        db.session.commit() # Save the updated values to the db.
        return redirect(url_for('home')) # Redirect to the home page.
    return render_template("edit.html",movie=movie, form=form)  # Render the edit page with the form.

# Define the delete route for removing a movie from the database.
@app.route("/delete")
def delete():
    movie_id = request.values.get('id') # Get the movie ID from the request.
    movie_id_to_delete = Movie.query.get(movie_id) # Fetch the movie from the database.
    db.session.delete(movie_id_to_delete) # Delete the movie.
    db.session.commit() # Save the changes.
    return redirect(url_for('home')) # Redirect to the home page.

# Define the add route for adding a new movie by searching TMDb API.
@app.route("/add", methods=['POST','GET'])
def add():
    form = MyMovieForm()
    if form.validate_on_submit(): # Process the form when submitted.
        movie_title = form.title.data # Retrieve the title from the form.
        response = requests.get(URL, params={"api_key": API_KEY, "query": movie_title}) # Connection with the API
        data = response.json()["results"] # Parse the response JSON.
        return render_template("select.html", options=data) # Render the select page with search results.
    return render_template("add.html", form=form) # Render the add page with the form.

# Define the find route for fetching detailed movie data from TMDb API.
@app.route("/find", methods=['POST','GET'])
def find():
    movie_id = request.values.get("id")
    if movie_id:
        movie_api_url = f"https://api.themoviedb.org/3/movie/{movie_id}?language=en-US"
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIxZjdhNTkzNzM4OGUyMWZmYzJmYWRhYjY4YWIwNzAxMCIsInN1YiI6IjY0Nzc1NjM3MTJjNjA0MDExZjY2NWNhOCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.U3fma2sTbfahEQIkUp4rjpIus7H7P0ty-jE5nH7ZVXw"
        }
        response = requests.get(movie_api_url, headers=headers)
        data = response.json()
        new_movie = Movie(
            title=data["original_title"],
            year=data["release_date"].split("-")[0],
            description=data["overview"],
            rating=data['vote_average'],
            ranking="",
            review="",
            img_url=f"{PICTURE_PATH}{data['poster_path']}"
        )
        db.session.add(new_movie)
        db.session.commit()
        form = MyRatingForm()
        
        return render_template("edit.html", form=form, movie=new_movie)

if __name__ == '__main__':
    app.run(debug=True)
