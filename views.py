from flask import Flask, render_template, request
from flask import redirect, jsonify, url_for, flash

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)


@app.route('/')
@app.route('/catalog')
def showCatalog():
    return "Catalog"


@app.route('/catalog/new')
def newCategory():
    return "New category"


@app.route('/catalog/<string:name>/edit')
def editCategory(name):
    return "Edit category %s" % name


@app.route('/catalog/<string:name>/delete')
def deleteCategory(name):
    return "Delete category %s" % name


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
