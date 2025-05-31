from flask import Flask,render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager,UserMixin
from datetime import datetime
from flask_login import login_required
from dotenv import load_dotenv
load_dotenv()
import os


class Base(DeclarativeBase):
  pass
app = Flask(__name__,static_url_path="/static")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI")
app.config["SECRET_KEY"] = "flask secret key to movie app password 2860987692870"
DEBUG=os.getenv("DEBUG")

db = SQLAlchemy(model_class=Base)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view="singin"

class User(db.Model,UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    comments = db.relationship("Comment", back_populates="user", lazy=True)
    favorite_movie = db.relationship("FavoriteMovie", back_populates="user", lazy=True)
class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(255), unique=False, nullable=False)
    movie_id=db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    user= db.relationship("User", back_populates="comments")

class FavoriteMovie(db.Model):
    _tablename_="favorites_movies"
    id = db.Column(db.Integer, primary_key=True)
    movie_id=db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    user= db.relationship("User", back_populates="favorite_movie")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)



with app.app_context():
    db.create_all()






users=[]


@app.route("/")
def index():
    from back import get_popular_movies,get_toprated_movies,get_upcoming_movies
    from flask_login import current_user
    popular_movies=get_popular_movies()
    top_rated_movies=get_toprated_movies()
    up_coming_movies=get_upcoming_movies()
    fav_movies = []
    if current_user.is_authenticated:
        fav_movies = [movie.movie_id for movie in current_user.favorite_movie]
        print("User favourite movies: ", fav_movies)
    return render_template("index.html",popular_movies=popular_movies,top_rated_movies=top_rated_movies,up_coming_movies=up_coming_movies,fav_movies=fav_movies   )


@app.route("/movies/<movies_type>")
def movies_list(movies_type: str):
    from back import get_popular_movies, get_upcoming_movies,get_toprated_movies
    from flask import request
    page=request.args.get("page", 1)
    if movies_type == "popular":
        movies = get_popular_movies()
    elif movies_type == "up coming":
        movies = get_upcoming_movies()
    elif movies_type == "toprated":
        movies = get_toprated_movies(page)
    else:
        movies = get_popular_movies()

    return render_template("movies_list.html", movies=movies)

@app.route("/movies/<movie_id>/details",methods=["GET", "POST"])
def movie_details(movie_id):
    from back import get_movie_details,get_image_details,get_videos,get_recomendation
    from flask import request
    from flask_login import current_user


    images=get_image_details(movie_id)
    data=get_movie_details(movie_id)
    videos=get_videos(movie_id)
    recomendation=get_recomendation(movie_id)
    filtered_videos = [
        video
        for video in videos
        if video.get("type", "") == "Trailer" and video.get("official", False)
    ]
    if request.method == "POST":
        content = request.form.get("content")
        print("Comment conmtent: ", content)
        comment=Comment(content=content,movie_id=movie_id,user=current_user)

    

        db.session.add(comment)
        db.session.commit()
    video_key = filtered_videos[0].get("key")
    video_key=videos[0].get("key")
    comments=Comment.query.filter_by(movie_id=movie_id).all()
   
    return render_template ("information.html",movie=data,images=images,video_key=video_key,recomendation=recomendation,comments=comments)
        
@app.route("/registration", methods=["GET", "POST"])
def registration():
    from flask import request,redirect
    if request.method == "POST":
        username=request.form.get("username")
        password=request.form.get("password")
        email=request.form.get("email")
        u = User.query.filter_by(username=username).first()
        print("Found user:", u)
        if len(password.strip()) < 8:
            return render_template(
                "registration.html",error="Password must be at least 8 characters long"
            )
        if len(username.strip()) < 3:
            return render_template(
                "registration.html",error="Username must be at least 3 characters long"
            )
        
        if User.query.filter_by(username=username).first():
            return render_template(
                "registration.html", error="Username already exists"
            )
        
        if User.query.filter_by(email=email).first():
            return render_template(
                "registration.html", error="Email already exists"
            )

        

        user=User(username=username,password=password,email=email)
        db.session.add(user)
        db.session.commit()

        return redirect("/signin")
    return render_template("registration.html")


@app.route("/movies/search")
def search_movies():
    from flask import request
    from back import search_movie

    query = request.args.get("query", "")
    print("Search query:", query)
    movies = search_movie(query)
    return render_template("movies_list.html", movies=movies)


@app.route("/signin", methods=["GET", "POST"])
def  singin ():
    from flask import request,redirect
    from flask_login import login_user

    if request.method == "POST":
        username=request.form.get("username")
        password=request.form.get("password")
        user=User.query.filter_by(username=username).first()
        if not user:
            return render_template("sign_in.html",error="User not found")
        if user.password != password:
            return render_template("sign_in.html",error="User not found")
        

        login_user(user)
        return redirect("/")


    
    return render_template ("sign_in.html")
@app.route("/logout")
def logout():
    from flask import  redirect
    from flask_login import logout_user
    logout_user()
    return redirect('/')

@app.route("/comments/<comment_id>/delete")
@login_required
def delete_comment(comment_id):
    from flask import redirect, request

    comment = Comment.query.filter_by(id=comment_id).first()
    if not comment:
        return "Comment not found. Try again!", 400

    db.session.delete(comment)
    db.session.commit()

    return redirect(request.referrer or "/")
@app.route("/movie/like/<movie_id>")
@login_required
def toggle_favourite_movie(movie_id):
    from flask_login import current_user
    from flask import redirect, request
    fav_movie =FavoriteMovie.query.filter_by(
        movie_id=movie_id, user=current_user
    ).first()
    if fav_movie:
        db.session.delete(fav_movie)
    else:
        fav_movie =FavoriteMovie(movie_id=movie_id, user=current_user)
        db.session.add(fav_movie)
    db.session.commit()
    return redirect(request.referrer or "/")

@app.route("/profile")
@login_required
def profile():
    from flask_login import current_user
    from back import get_movie_details
    favorite_movies=[
        get_movie_details(m.movie_id) for m in current_user.favorite_movie
    ]
   
    return render_template("profile.html",favorite_movies=favorite_movies)
 
# app.run(debug=DEBUG)
