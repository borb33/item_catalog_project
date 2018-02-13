import os
import datetime
from flask import Flask, render_template, request
from flask import redirect, jsonify, url_for, flash
from flask import send_from_directory
from werkzeug.utils import secure_filename

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from models import Base, Category, Item, User

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Check if the file extension is valid
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


# HTML Endpoints
@app.route('/')
@app.route('/catalog')
def showCatalog():
    return render_template('catalog.html')


@app.route('/catalog/<string:name>')
def showCategory(name):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(name=name).one()
    return render_template('category.html',
                           categories=categories, category=category)


@app.route('/catalog/new', methods=['GET', 'POST'])
def newCategory():
    categories = session.query(Category).all()
    if request.method == 'POST':
        # Upload file
        file = request.files['file']
        name = request.form['name']
        description = request.form['description']

        if file.filename == '' or name == '' or description == '':
            # ERROR MESSAGE
            return redirect(request.url)

        if file and allowed_file(file.filename):
            now = datetime.datetime.now()
            filename = ''.join([now.strftime("%Y%m%d%H%M_"),
                               secure_filename(file.filename)])
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        elif not allowed_file(file.filename):
            # ERROR MESSAGE
            return redirect(request.url)

        category = Category(
            name=name,
            description=description,
            image=filename
        )
        session.add(category)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return render_template('newCategory.html', categories=categories)


@app.route('/catalog/<string:name>/edit', methods=['GET', 'POST'])
def editCategory(name):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(name=name).one()
    if request.method == 'POST':
        # Upload file
        file = request.files['file']
        name = request.form['name']
        description = request.form['description']

        if file.filename != '' and allowed_file(file.filename):
            now = datetime.datetime.now()
            filename = ''.join([now.strftime("%Y%m%d%H%M_"),
                               secure_filename(file.filename)])
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        elif file.filename != '' and not allowed_file(file.filename):
            # ERROR MESSAGE
            return redirect(request.url)

        if name:
            category.name = name
        if description:
            category.description = description
        if file.filename != '':
            category.image = filename

        session.add(category)
        session.commit()
        return redirect(url_for('showCategory', name=name))
    else:
        return render_template('editCategory.html',
                               categories=categories, category=category)


@app.route('/catalog/<int:id>/delete', methods=['POST'])
def deleteCategory(id):
    category = session.query(Category).filter_by(id=id).one()
    if request.method == 'POST':
        session.delete(category)
        session.commit()
        return 'OK'


@app.route('/catalog/<string:name>/new')
def newItem(name):
    return "New item for category %s" % name


@app.route('/catalog/<string:name>/<string:item>/edit')
def editItem(name, item):
    return "Edit item %s from category %s" % (item, name)


@app.route('/catalog/<string:name>/<string:item>/delete')
def deleteItem(name, item):
    return "Delete item %s from category %s" % (item, name)


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
