import os
from flask import Flask, render_template, request, jsonify, abort, session, redirect, url_for
from sqlalchemy import exc
import json 
import flask_cors
from flask_cors import CORS
from flask_cors import cross_origin
from authlib.integrations.flask_client import OAuth
from urllib.parse import quote_plus, urlencode
from database.models import db_drop_and_create_all, setup_db, Movie, Actor
from auth.auth import AuthError, requires_auth, auth_register

import requests
from requests.structures import CaseInsensitiveDict
from authlib.integrations.flask_client import OAuth
from os import environ as env
from flask_wtf import Form
from forms import * 

app = Flask(__name__, template_folder='template')
app.secret_key = env.get("APP_SECRET_KEY").encode('utf8') 
app.app_context().push()
setup_db(app)
CORS(app)
oauth = OAuth(app)
    
''' 
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one 
'''
db_drop_and_create_all()
auth_register(oauth)


@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for('callback', _external=True)
    )

@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    print("token")
    print(token)
    session["user"] = token
    return redirect("/")

@app.route("/")
# @requires_auth(session, 'get:movie')
def home():
    return render_template('home.html', session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN") 
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

@app.route('/actors', methods=['GET'])
@requires_auth(session, 'get:actor')
def get_actors(jwt):
    if request.method == 'GET':
        print("Inside get actors") 
        all_actors = Actor.query.all() 
        actors = []
        if len(all_actors) == 0: 
            abort(404)
    
        print(len(all_actors))
        print(type(all_actors[0]))
        for d in all_actors:
            actors.append(d.retrive())
    
        return render_template('actors.html', actors=actors);

@app.route('/actors/create', methods=['GET', 'POST'])
@requires_auth(session, 'post:actor')
def create_actor(jwt):
    if request.method == 'GET':
        print("Inside actor create get method")
        form = ActorForm()
        return render_template('forms/new_actor.html', form=form)
    elif request.method == 'POST':
        print("Inside actor create POST method")
        try:
            # request_bar = request.get_json() 
            data = request.form
            print(data.getlist('name')[0])
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print(message)
        name = data.getlist('name')[0]
        print(name)
        age = data.getlist('age')[0]
        print(age)
        gender = data.getlist('gender')[0]
        print(gender)
        if data == 'null': 
            abort(400) 
        try:
            new_actor = Actor(name = name, age = age, gender=gender)
            new_actor.insert()
            new_actor = [new_actor.retrive()]
            # return jsonify({'success': True, 'actors': new_actor}), 200
            return redirect('/actors')
        except:
            return json.dumps({'success': False, 'error': "An error occurred" }), 500

@app.route('/actors/update', methods=['GET', 'POST'])
@requires_auth(session, 'patch:actor')
def update_actor(jwt):
    print("Inside actor update method")
    if request.method == 'GET':
        print("Inside actor update get method")
        all_actors = Actor.query.all()
        actors = []

        if len(all_actors) == 0:
            abort(404)
    
        print(type(all_actors[0]))
        for d in all_actors:
            print(d.retrive())
            actors.append(d.retrive())
        form = ActorForm()
        return render_template('forms/update_actor.html', form=form, actors=actors)
    if request.method == 'POST':
        data = request.form

        print(data.getlist('actors')[0])
        id = data.getlist('actors')[0]
        actor = Actor()
        actor = Actor.query.filter(Actor.id == id).one_or_none()
        print(actor.name)
        print(actor.age)
        print(actor.gender)
    if actor is None:
        abort(404)

    try:
        if data.getlist('name')[0] != "":
            actor.name = data.getlist('name')[0]
        
        if data.getlist('age')[0] != "":
            actor.age =  data.getlist('age')[0]

        if data.getlist('gender')[0] != "":
            actor.gender = data.getlist('gender')[0]

        print(data.getlist('name')[0])   
        print(data.getlist('age')[0])   
        print(data.getlist('gender')[0])   
        actor.update()
        print("actor.name") 
        actor = [actor.retrive()]
        # return jsonify({'success': True, 'movies': movie}), 200
        return redirect('/actors')
    except:
        return json.dumps({'success': False, 'error': "An error occurred" }), 500 

@app.route('/actors/delete', methods=['GET', 'POST', 'DELETE'])
@requires_auth(session, 'delete:actor')
def delete_actor(jwt):
    print("inside delete")
    if request.method == 'GET':
        print("Inside actor delete get method")
        all_actors = Actor.query.all()
        actors = []

        if len(all_actors) == 0:  
            abort(404)
    
        print(type(all_actors[0]))
        for d in all_actors:
            print(d.retrive())
            actors.append(d.retrive())
        return render_template('forms/delete_actor.html', actors=actors)
    elif request.method == 'POST':
        print("Inside actor delete post method")
        option = request.form['actors']
        print(option)
        actor = Actor.query.filter(Actor.id == option).one_or_none()
        print(actor)
        if actor is None:
             abort(404)

        try:
            actor.delete()
            # return jsonify({'success': True, 'delete': option}), 200
            return redirect('/actors')

        except:
            return json.dumps({'success': False, 'error': "An error occurred" }), 500

@app.route('/movies', methods=['GET'])
@requires_auth(session, 'get:movie')
def get_movies(jwt):
    if request.method == 'GET':
        print("Inside get movies") 
        
        all_movies = Movie.query.all() 
        movies = []

        if len(all_movies) == 0:  
            abort(404)
    
        print(type(all_movies[0]))
        for d in all_movies:
            dr = d.retrive()
            if dr.get('actors') is not None:
                actor = Actor.query.filter(Actor.id == dr.get('actors')).one_or_none()
                print(actor.retrive().get('name'))
                dr.update({"title": "Sara"})
                dr.update({"actors": actor.retrive().get('name')})
                print(dr)
            movies.append(dr)
            
            # movies = [d.retrive()]
    
        # return jsonify({
        #     "success": True, 
        #     "movies": movies
        # }), 200
        return render_template('movies.html', movies=movies);

@app.route('/movies/create', methods=['GET', 'POST'])
@requires_auth(session, 'post:movie')
def create_movie(jwt):
    if request.method == 'GET':
        print("Inside movie create get method")
        form = MovieForm()
        all_actors = Actor.query.all()
        actors = []

        if len(all_actors) == 0:  
            abort(404)
    
        print(type(all_actors[0]))
        for d in all_actors:
            print(d.retrive())
            actors.append(d.retrive())
        return render_template('forms/new_movie.html', form=form, actors=actors)
    elif request.method == 'POST':
        print("Inside movie create POST method")
        try:
            # request_bar = request.get_json() 
            data = request.form
            print(data.getlist('title')[0])
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print(message)
        title = data.getlist('title')[0]
        print(title)
        release_date = data.getlist('release_date')[0]
        print(release_date)
        actors = data.getlist('actors')[0]
        if data == 'null': 
            abort(400) 
        try:
            new_movie = Movie(title = title, release_date = release_date, actors = actors)
            # new_movie.title = title 
            # new_movie.release_date =  json.dumps(release_date)
            new_movie.insert()
            new_movie = [new_movie.retrive()]
            # return jsonify({'success': True, 'movies': new_movie}), 200
            return redirect('/movies')
        except:
            return json.dumps({'success': False, 'error': "An error occurred" }), 500

@app.route('/movies/update', methods=['GET', 'POST'])
@requires_auth(session, 'patch:movie')
def update_movie(jwt):
    print("Inside movie update get method")
    if request.method == 'GET':
        print("Inside movie update get method")
        all_movies = Movie.query.all()
        movies = []

        if len(all_movies) == 0:
            abort(404)
    
        print(type(all_movies[0]))
        for d in all_movies:
            print(d.retrive())
            movies.append(d.retrive())
        form = MovieForm()
        return render_template('forms/update_movie.html', form=form, movies=movies)
    if request.method == 'POST':
        data = request.form

        print(data.getlist('movies')[0])
        id = data.getlist('movies')[0]
        movie = Movie()
        movie = Movie.query.filter(Movie.id == id).one_or_none()
    if movie is None:
        abort(404)

    try:
        if data.getlist('title')[0] is not None:
            movie.title = data.getlist('title')[0]
        
        if data.getlist('release_date')[0] is not None:
            movie.release_date =  json.dumps([data.getlist('release_date')[0]])
               
        movie.update()
        movie = [movie.retrive()]
        # return jsonify({'success': True, 'movies': movie}), 200
        return redirect('/movies')
    except:
        return json.dumps({'success': False, 'error': "An error occurred" }), 500 

@app.route('/movies/delete', methods=['GET', 'POST', 'DELETE'])
@requires_auth(session, 'delete:movie')
def delete_movie(jwt):
    print("inside delete")
    if request.method == 'GET':
        print("Inside movie delete get method")
        all_movies = Movie.query.all()
        movies = []

        if len(all_movies) == 0:  
            abort(404)
    
        print(type(all_movies[0]))
        for d in all_movies:
            print(d.retrive())
            movies.append(d.retrive())
        return render_template('forms/delete_movie.html', movies=movies)
    elif request.method == 'POST':
        print("Inside movie delete post method")
        option = request.form['movies']
        print(option)
        movie = Movie.query.filter(Movie.id == option).one_or_none()
        print(movie)
        if movie is None:
             abort(404)

        try:
            movie.delete()
            # return jsonify({'success': True, 'delete': option}), 200
            return redirect('/movies')

        except:
            return json.dumps({'success': False, 'error': "An error occurred" }), 500

'''
Error handling 
'''
@app.errorhandler(401)
def unprocessable(error):
    # return jsonify({
    #     "success": False,
    #     "error": 401,
    #     "message": "Permission Not found"
    # }), 401
    return render_template('error.html', error=error, message= "401-You are not authorized!!!")


@app.errorhandler(422)
def unprocessable(error):
    # return jsonify({
    #     "success": False,
    #     "error": 422,
    #     "message": "unprocessable"
    # }), 422
    return render_template('error.html', error=error, message= "422-Unprocessable!!")

@app.errorhandler(404)
def resource_not_found(error):
    # return jsonify({
    #     "success": False,
    #     "error": 404,
    #     "message": "resource not found"
    # }), 404
    return render_template('error.html', error=error, message= "404-Resource not found!!")

@app.errorhandler(400)
def bad_request(error):
    # return jsonify({
    #     "success": False,
    #     "error": 400,
    #     "message": 'Bad Request'
    # }), 400
    return render_template('error.html', error=error, message= "400-Bad Request!!")

@app.errorhandler(405)
def method_not_allowed(error):
    # print(error)
    # return jsonify({
    #     "success": False,
    #     "error": 405,
    #     "message": 'Method Not Allowed'
    # }), 405
    return render_template('error.html', error=error, message= "405-Method Not Allowed!!")

@app.errorhandler(403)
def permission_not_present(error):
    # return jsonify({
    #     "success": False,
    #     "error": 403,
    #     "message": 'Permission Not Present'
    # }), 403    
    return render_template('error.html', error=error, message= "403-Permission Not Found!!")

@app.errorhandler(500)
def error_present(error):
    # return jsonify({
    #     "success": False,
    #     "error": 500,
    #     "message": 'An error occurred'
    # }), 500
    return render_template('error.html', error=error, message= "500-An error occurred!!")