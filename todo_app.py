from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import sys

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:Ropac123@localhost:5432/todoapp'
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Todo(db.Model):
    __tablename__ = 'todos'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    list_id = db.Column(db.Integer, db.ForeignKey('todolists.id'), nullable=False)

    def __repr__(self):
        return f'<Todo ID: {self.id} -> {self.description}, {self.completed}, {self.list_id}\n>'


class TodoList(db.Model):
    __tablename__ = 'todolists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    todos = db.relationship('Todo', backref='todo_list', lazy=True)

    def __repr__(self):
        return f'<Todo List: {self.id} -> {self.name}>\n'


# db.create_all()

@app.route('/lists/<list_id>')
def get_todo_items(list_id):
    return render_template('index.html',
                           todos=Todo.query.filter_by(list_id=list_id).order_by(Todo.id).all(),
                           active_list=TodoList.query.get(list_id),
                           lists=TodoList.query.order_by(TodoList.id).all())


@app.route('/')
def index():
    list_id = TodoList.query.filter(TodoList.name.ilike('uncategorized')).order_by(TodoList.id).limit(1).all()[0].id
    return redirect(url_for('get_todo_items', list_id=list_id))


@app.route('/todos/create/synchronous', methods=['POST'])
def create_todo_synchoronous():
    description = request.form['description']
    db.session.add(Todo(description=description))
    db.session.commit()
    return redirect(url_for('index'))
    # return render_template('index1.html', data=Todo.query.all())


@app.route('/todos/create/asynchronous/<list_id>', methods=['POST'])
def create_todo_asynchoronous(list_id):
    error = False
    body = {}
    try:
        description = request.get_json()['description']
        todo = Todo(description=description, list_id=list_id)
        db.session.add(todo)
        db.session.commit()
        body['description'] = description
    except:
        error = True
        db.session.rollback()
        print(sys.exec_info())
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return jsonify(body)


@app.route('/lists/create/asynchronous', methods=['POST'])
def create_list_asynchronous():
    body = {}
    error = False
    try:
        name = request.get_json()['name']
        list = TodoList(name=name)
        db.session.add(list)
        db.session.commit()
        body['name'] = name
    except:
        error = True
        db.session.rollback()
        print(sys.exec_info())
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return jsonify(body)


@app.route('/todos/<todo_id>/set-completed', methods=['POST'])
def edit_completed(todo_id):
    try:
        completed = Todo.query.get(todo_id).completed
        new_completed = not completed
        Todo.query.get(todo_id).completed = new_completed
        db.session.commit()
    except:
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    return redirect(url_for('index'))


@app.route('/todos/<todo_id>/delete', methods=['POST'])
def delete_todo(todo_id):
    error = False
    try:
        todo = Todo.query.get(todo_id)
        db.session.delete(todo)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    return jsonify({
        'success': not error
    })

# return render_template('index.html', data=[{
#     'description': 'Todo 1'
# }, {
#     'description': 'Todo 2'
# }, {
#     'description': 'Todo 3'
# }])
