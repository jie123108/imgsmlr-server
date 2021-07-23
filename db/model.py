from sqlalchemy import Column, Integer, String, REAL, BIGINT, SMALLINT, INTEGER, TEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
import sqlalchemy.types as types
import json

def signature_preprocess(signature):
    strvalue = json.dumps(signature)
    return strvalue.replace('[', '(').replace(']', ')')

def pattern_preprocess(pattern):
    strvalue = json.dumps(pattern)
    return strvalue.replace('[', '(').replace(']', ')')

class Signature(types.UserDefinedType):
    def __init__(self):
        pass

    def get_col_spec(self, **kw):
        return "signature[16]"

    def bind_processor(self, dialect):
        def process(value):
            return signature_preprocess(value)
        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            if value:
                value = value.replace('(', '[').replace(')', ']')
                value = json.loads(value)
            return value
        return process

class Pattern(types.UserDefinedType):
    def __init__(self):
        pass

    def get_col_spec(self, **kw):
        return "pattern[64][64]"

    def bind_processor(self, dialect):
        def process(value):
            return pattern_preprocess(value)
        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            if value:
                value = value.replace('(', '[').replace(')', ']')
                value = json.loads(value)
            return value
        return process


Base = declarative_base()

def as_dict(obj):
    dictret = dict(obj.__dict__);
    dictret.pop('_sa_instance_state', None)
    return dictret

class Image(Base):
    __tablename__ = 'image'

    id = Column("id", INTEGER, primary_key=True)
    url = Column("url", TEXT)
    md5 = Column("md5", TEXT)
    pattern = Column("pattern", Pattern)
    signature = Column(Signature)
    remark = Column(TEXT)
    dataId = Column("data_id", TEXT)
    meta = Column(JSONB)

    def __repr__(self):
       return "<Image{id='%s', url='%s', md5='%s'}>" % (self.id, self.url, self.md5)

    def as_dict(self):
        return as_dict(self)
