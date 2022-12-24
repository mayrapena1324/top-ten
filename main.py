from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import requests
import os

API_KEY = os.environ.get("MY_API_KEY")

API_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'SECRET_APP_KEY'
Bootstrap(app)

# CREATE DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movie-collection.db"
# Optional: But it will silence the deprecation warning in the console.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class AddMovie(FlaskForm):
    title = StringField(label="Movie Title", validators=[DataRequired()])
    submit = SubmitField(label="Add Movie")

# created a class using FlaskForm
class RateMovieForm(FlaskForm):
    # label is what will be displayed
    rating = FloatField(label="Your rating out of 10 e.g 7.5", validators=[DataRequired()])
    review = StringField(label="Your review", validators=[DataRequired()])
    submit = SubmitField(label="Done")


# CREATE TABLE
class Movies(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(350), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(500), nullable=True)
    img_url = db.Column(db.String(500), nullable=False)

# Allow each book object to be identified by its title when printed.
    def __repr__(self):
        return f'<Movie {self.title}>'


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    # This line creates a list of all the movies sorted by rating
    all_movies = Movies.query.order_by(Movies.rating).all()

    # This line loops through all the movies
    for i in range(len(all_movies)):
        # This line gives each movie a new ranking reversed from their order in all_movies
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def rate_movie():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie_selected = Movies.query.get(movie_id)
    if request.method == "POST":
        # UPDATE RECORD
        movie_to_update = Movies.query.get(movie_id)
        movie_to_update.rating = request.form["rating"]
        movie_to_update.review = request.form["review"]
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=form, movie=movie_selected)


@app.route("/delete")
def delete():
    movie_id = request.args.get('id')
    movie_to_delete = Movies.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    form = AddMovie()
    if request.method == "POST":
        parameters = {
            "api_key": API_KEY,
            "query": form.title.data,
        }
        movies_response = requests.get(url=API_URL, params=parameters).json()
        print(movies_response)
        return render_template("select.html", form=form, movies=movies_response, key=API_KEY)
    return render_template("add.html", form=form)


@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"https://api.themoviedb.org/3/movie/{movie_api_id}"
        response = requests.get(movie_api_url, params={"api_key": API_KEY, "language": "en-US"})
        data = response.json()
        print(data)
        new_movie = Movies(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"]
        )

        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("rate_movie", id=new_movie.id))


if __name__ == '__main__':
    app.run(port=4999, debug=True)