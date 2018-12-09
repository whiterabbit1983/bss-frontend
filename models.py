from peewee import *


db = SqliteDatabase('tasks.db')


class Scenario(Model):
    name = CharField()
    creation_date = DateTimeField()
    last_execution_date = DateTimeField()
    last_result = CharField()
    language = CharField()
    program = TextField()

    class Meta:
        database = db
