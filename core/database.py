from peewee import *
from flask import Flask

db = SqliteDatabase('tickets.db')

def iter_tables(model_dict):
    for key in model_dict:
        if not db.table_exists(key):
            db.connect(reuse_if_open=True)
            db.create_tables([model_dict[key]])
            db.close()

class BaseModel(Model):

    class Meta:
        database = db

class TInfo(BaseModel):
    id = AutoField()
    ServerId = TextField()
    TicketCount = IntegerField()
    ChannelList = TextField()

class UInfo(BaseModel):
    id = AutoField()
    UserId = TextField()
    TicketCount = IntegerField()

app = Flask(__name__)

@app.before_request
def _db_connect():
    db.connect()

@app.teardown_request
def _db_close(exc):
    if not db.is_closed():
        db.close()

tables = {"TicketInfo":TInfo, "UserInfo":UInfo}
iter_tables(tables)