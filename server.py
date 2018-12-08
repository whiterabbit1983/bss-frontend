import click
from flask import Flask
from flask_restful import Resource, Api, reqparse, abort
from flask_rabbitmq import Queue, RabbitMQ


app = Flask(__name__)


class TaskList(Resource):
    def __init__(self, *args, **kwargs):
        self.parser = parser = reqparse.RequestParser()
        parser.add_argument('task')

    def get(self):
        # get a list of tasks
        pass

    def post(self):
        args = self.parser.parse_args()
        task = args.get('task', None)
        if not task:
            abort(400, message='Task is not set')
        # TODO: put to rabbitmq
        response = {'result': 1}
        return response, 201


class Task(Resource):
    def get(self, task_id):
        pass
    
    def delete(self, task_id):
        pass


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
    return 'Any String'


@click.command()
@click.option('-c', '--rabbitmq-config', help='RabbitMQ config file', required=True)
def main(rabbitmq_config):
    app.config.from_object(f'{rabbitmq_config}.RabbitMQConfig')
    # create REST endpoints
    api = Api(app)
    api.add_resource(TaskList, '/tasks')
    api.add_resource(Task, '/tasks/<task_id>')
    api.add_resource(Plugins, '/plugins')
    # create RabbitMQ queue
    queue = Queue()
    rpc = RabbitMQ(app, queue)
    rpc.run()
    # start the app
    app.run()


if __name__ == '__main__':
    main()
