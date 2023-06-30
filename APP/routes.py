from flask import render_template, url_for, flash, redirect, request, abort
from flask_login import login_user, current_user, logout_user, login_required
from flask_share import Share
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash
from random import randint
from .models import User, Url
import random, string, io, qrcode
from flask import request
import qrcode
import io
import shortuuid
from . import app, db, mail, cache



@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user:
            if user and check_password_hash(user.password, password):
                login_user(user)
                flash('You are now logged in.')
                return redirect(url_for('home'))
            
            if (user and check_password_hash(user.password, password)) == False:
                flash('Please provide valid credentials.')
                return redirect(url_for('login'))

        else:
            flash('Account not found. Please sign up to continue.')
            return redirect(url_for('signup'))
        
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        username_exists = User.query.filter_by(username=username).first()
        if username_exists:
            flash('This username already exists.')
            return redirect(url_for('home'))

        email_exists = User.query.filter_by(email=email).first()
        if email_exists:
            flash('This email is already registered.')
            return redirect(url_for('signup'))

        password = generate_password_hash(password)

        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash('You are now signed up.')
        return redirect(url_for('login'))

    return render_template('signup.html')


def generate_qr_code(url):
    img = qrcode.make(url)
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return img_io


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        long_url = request.form['long_url']
        custom_url = request.form['custom_url'] or None
        if custom_url:
            existing_url = Url.query.filter_by(custom_url=custom_url).first()
            if existing_url:
                flash ('That custom URL already exists. Please try another one!')
                return redirect(url_for('home'))
            short_url = custom_url
        elif long_url[:4] != 'http':
            long_url = 'http://' + long_url
        else:
            short_url = shortuuid.uuid()[:6]
        url = Url(long_url=long_url, short_url=short_url, custom_url=custom_url, user_id=current_user.id)
        db.session.add(url)
        db.session.commit()
        return redirect(url_for('dashboard'))

    urls = Url.query.order_by(Url.created_at.desc()).limit(10).all()
    return render_template('index.html', urls=urls)

@app.route("/dashboard")
@login_required
@cache.cached(timeout=50)
def dashboard():
    urls = Url.query.filter_by(user_id=current_user.id).order_by(Url.created_at.desc()).all()
    host = request.host_url
    return render_template('dashboard.html', urls=urls, host=host)

@app.route("/about")
def about():
    return render_template('about.html')

@app.route('/<short_url>')
@cache.cached(timeout=30)
def redirect_url(short_url):
    url = Url.query.filter_by(short_url=short_url).first()
    if url:
        url.clicks += 1
        db.session.commit()
        return redirect(url.long_url)
    return 'URL not found.'

@app.route('/qr_code/<short_url>')
def generate_qr_code_url(short_url):
    url = Url.query.filter_by(short_url=short_url).first()
    if url:
        img_io = generate_qr_code(request.host_url + url.short_url)
        return img_io.getvalue(), 200, {'Content-Type': 'image/png'}
    return 'URL not found.'

@app.route('/analytics/<short_url>')
@login_required
@cache.cached(timeout=50)
def url_analytics(short_url):
    url = Url.query.filter_by(short_url=short_url).first()
    if url:
        return render_template('analytics.html', url=url)
    return 'URL not found.'

@app.route('/history')
@login_required
@cache.cached(timeout=50)
def link_history():
    urls = Url.query.filter_by(user_id=current_user.id).order_by(Url.created_at.desc()).all()
    host = request.host_url
    return render_template('history.html', urls=urls, host=host)

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    url = Url.query.get_or_404(id)
    if url:
        db.session.delete(url)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return 'URL not found.'

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_url(id):
    url = Url.query.get_or_404(id)
    if url:
        if request.method == 'POST':
            custom_url = request.form['custom_url']
            if custom_url:
                existing_url = Url.query.filter_by(custom_url=custom_url).first()
                if existing_url:
                    flash ('That custom URL already exists. Please try another one.')
                    return redirect(url_for('edit_url', id=id))
                url.custom_url = custom_url
                url.short_url = custom_url
            db.session.commit()
            return redirect(url_for('dashboard'))
        return render_template('edit.html', url=url)
    return 'URL not found.'
