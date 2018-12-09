import os
import json
import time
import click
import parsers
import pkgutil
import threading
import parsers
import firebase_admin
from datetime import datetime
from flask import Flask, Blueprint, render_template, request, redirect, abort, url_for
from werkzeug.utils import secure_filename
from flask_restful import Resource, Api, reqparse, abort
from flask_rabbitmq import Queue, RabbitMQ
from firebase_admin import credentials, firestore
from models import db, Scenario


app = Flask(__name__)
scenarios_bp = Blueprint('scenarios', __name__, url_prefix='/scenarios')
plugins_bp = Blueprint('plugins', __name__, url_prefix='/plugins')

# firestore
cred = credentials.Certificate('./ServiceAccount.json')
firebase_admin.initialize_app(cred)
firestore_db = firestore.client()


class RMQ:
    def __init__(self):
        self.rpc = None
        self.queue = None

    def start(self, app, rabbitmq_config):
        app.config.from_object(f'{rabbitmq_config}.RabbitMQConfig')
        self.queue = queue = Queue()
        self.rpc = rpc = RabbitMQ(app, queue)
        rpc.run()


rmq = RMQ()


# TODO: finish
class Scheduler(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.evt = threading.Event()
        self._q = []

    def add_job(self, job):
        pass

    def stop(self):
        self.evt.set()

    def run(self):
        while not self.evt.is_set():
            time.sleep(1)
            now = datetime.now()


scheduler = Scheduler()


def languages():
    return [p.name for p in pkgutil.iter_modules(parsers.__path__)]


class TaskList(Resource):
    def __init__(self, *args, **kwargs):
        self.parser = parser = reqparse.RequestParser()
        parser.add_argument('task')
        parser.add_argument('language')

    def post(self):
        args = self.parser.parse_args()
        task = args.get('task', None)
        language = args.get('language', 'python')
        if not task:
            abort(400, message='Task is not set')
        compiler = getattr(parsers, language, None)
        if not compiler:
            abort(400, message=f'Unknown language {language}')
        compiled_json = compiler.compile(task)
        response = rmq.rpc.send_sync(str(compiled_json), '', 'exec')
        if isinstance(response, bytes):
            response = response.decode()
        return json.loads(response)[0], 201


class Plugins(Resource):
    def __init__(self, *args, **kwargs):
        self.parser = parser = reqparse.RequestParser()
        parser.add_argument('name')
        parser.add_argument('description')
        parser.add_argument('author')
        parser.add_argument('name')

    def get(self):
        # get list of plugins
        pass
    
    def post(self):
        # add plugin
        pass


@app.route('/')
def index():
    # main page
    return render_template('start.html')


@scenarios_bp.route('/<int:task_id>', methods=('GET', 'POST'))
def edit_scenario(task_id):
    try:
        scenario = Scenario.get_by_id(task_id)
    except Exception:
        abort(404)
    else:
        if not scenario:
            abort(404)
    return render_template('scenarios/create.html', languages=languages(), scenario=scenario)


@scenarios_bp.route('/create', methods=('GET', 'POST'))
def add_scenario():
    # show add task form
    if request.method == 'GET':
        return render_template('scenarios/create.html', languages=languages(), scenario=None)
    else:
        task_id = request.form.get('task_id', None)
        if not task_id:
            scenario = Scenario(
                name=request.form['name'],
                creation_date=datetime.now(),
                last_execution_date=datetime.now(),
                last_result='',
                language=request.form['language'],
                program=request.form['source']
            )
            scenario.save()
        else:
            scenario = Scenario.get_by_id(int(task_id))
            if scenario:
                scenario.name = request.form['name']
                scenario.language = language=request.form['language']
                scenario.program = request.form['source']
                scenario.save()
        
        return redirect(url_for('scenarios.list_scenarios'))


@scenarios_bp.route('/list', methods=('GET',))
def list_scenarios():
    scenarios = Scenario.select().execute()
    return render_template('scenarios/list.html', scenarios=scenarios)


@plugins_bp.route('/list', methods=('GET',))
def list_plugins():
    # show list of plugins
    plugins_ref = firestore_db.collection('plugins')
    plugins = [p.id for p in plugins_ref.get()]
    return render_template('plugins/list.html', plugins=plugins)


@plugins_bp.route('/add', methods=('GET', 'POST'))
def add_plugin():
    # add plugin form
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(full_path)
            # save to firebase
            doc_ref = firestore_db.collection('plugins').document(filename)
            doc_ref.set({'body': open(full_path, 'rb').read()})
            return redirect(url_for('plugins.list_plugins'))
    return render_template('plugins/add.html')


@click.command()
@click.option('-c', '--rabbitmq-config', help='RabbitMQ config file', required=True)
def main(rabbitmq_config):
    # setup database
    db.connect()
    db.create_tables([Scenario])
    # setup app
    # app.config.from_object(f'{rabbitmq_config}.RabbitMQConfig')
    app.register_blueprint(scenarios_bp)
    app.register_blueprint(plugins_bp)
    # create REST endpoints
    api = Api(app)
    api.add_resource(TaskList, '/tasks')
    api.add_resource(Plugins, '/plugins')
    # create RabbitMQ queue
    rmq.start(app, rabbitmq_config)
    # queue = Queue()
    # rpc = RabbitMQ(app, queue)
    # rpc.run()
    # start task scheduler
    # scheduler.start()
    # start the app
    app.run()


if __name__ == '__main__':
    main()
