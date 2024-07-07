from app import db
from sqlalchemy_utils import JSONType
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.dialects.postgresql import ARRAY

class SessionData(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    conversation_id = db.Column(db.String, unique=True)
    prompt_type = db.Column(db.String)
    messages = db.Column(MutableDict.as_mutable(JSONType), default={})
    convo = db.Column(db.String)
    messages_array = db.Column(ARRAY(db.JSON), nullable=False, default=[])

class Questions(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    question = db.Column(db.String(2500), nullable=False)
    answer = db.Column(db.String(10000), nullable=False)
    type = db.Column(db.String(100), nullable=True)

class SystemStartMessages(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    message = db.Column(db.String(20000), nullable=False)