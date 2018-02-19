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


# Upload file
def upload_file(file):
    if file and allowed_file(file.filename):
        now = datetime.datetime.now()
        filename = ''.join([now.strftime("%Y%m%d%H%M_"),
                            secure_filename(file.filename)])
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    elif not allowed_file(file.filename):
        # ERROR MESSAGE
        return False
    return filename


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
    items = session.query(Item).filter_by(category_id=category.id).all()
    return render_template('category.html',
                           categories=categories,
                           category=category,
                           items=items)


@app.route('/catalog/new', methods=['GET', 'POST'])
def newCategory():
    categories = session.query(Category).all()
    if request.method == 'POST':
        file = request.files['file']
        name = request.form['name']
        description = request.form['description']

        if name == '' or description == '' or file.filename == '':
            # ERROR MESSAGE
            return redirect(request.url)

        filename = upload_file(file)

        if not filename:
            return redirect(request.url)

        category = Category(
            name=name,
            description=description,
            image=filename
        )
        session.add(category)
        session.commit()
        return redirect(url_for('showCategory', name=name))
    else:
        return render_template('newCategory.html', categories=categories)


@app.route('/catalog/<string:name>/edit', methods=['GET', 'POST'])
def editCategory(name):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(name=name).one()
    if request.method == 'POST':
        file = request.files['file']
        name = request.form['name']
        description = request.form['description']

        if file.filename != '':
            filename = upload_file(file)
            if filename:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'],
                                       category.image))
            else:
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
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], category.image))
        session.delete(category)
        session.commit()
        return 'OK'


@app.route('/catalog/<string:name>/new', methods=['GET', 'POST'])
def newItem(name):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(name=name).one()
    if request.method == 'POST':
        file = request.files['file']
        name = request.form['name']
        description = request.form['description']

        # Check if the name is already used
        try:
            newItem = session.query(Item).filter_by(
                name=name, category_id=category.id).one()
            if newItem:
                # ERROR MESSAGE
                return redirect(request.url)
        except:
            pass

        if name == '' or description == '' or file.filename == '':
            # ERROR MESSAGE
            return redirect(request.url)

        filename = upload_file(file)

        if not filename:
            return redirect(request.url)

        item = Item(
            name=name,
            image=filename,
            description=description,
            category_id=category.id
        )
        session.add(item)
        session.commit()
        return redirect(url_for('showCategory', name=category.name))
    else:
        return render_template('newItem.html',
                               categories=categories, category=category)


@app.route('/catalog/<string:name>/<string:item>/edit',
           methods=['GET', 'POST'])
def editItem(name, item):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(name=name).one()
    item = session.query(Item).filter_by(name=item,
                                         category_id=category.id).one()
    if request.method == 'POST':
        file = request.files['file']
        name = request.form['name']
        description = request.form['description']

        # Check if the name is already used
        try:
            newItem = session.query(Item).filter_by(
                name=name, category_id=category.id).one()
            if newItem.name != item.name:
                # ERROR MESSAGE
                return redirect(request.url)
        except:
            pass

        if file.filename != '':
            filename = upload_file(file)
            if filename:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'],
                                       item.image))
            else:
                # ERROR MESSAGE
                return redirect(request.url)

        if name:
            item.name = name
        if description:
            item.description = description
        if file.filename != '':
            item.image = filename

        session.add(item)
        session.commit()
        return redirect(url_for('showCategory', name=category.name))
    else:
        return render_template('editItem.html',
                               categories=categories,
                               category=category,
                               item=item)


@app.route('/catalog/<string:name>/<int:id>/delete', methods=['POST'])
def deleteItem(name, id):
    item = session.query(Item).filter_by(id=id).one()
    if request.method == 'POST':
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], item.image))
        session.delete(item)
        session.commit()
        return 'OK'


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
