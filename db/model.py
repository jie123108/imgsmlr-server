from sqlalchemy import Column, Integer, String, REAL, BIGINT, SMALLINT, INTEGER, TEXT, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
import sqlalchemy.types as types
from pgvector.sqlalchemy import Vector
import numpy
import json
from datetime import datetime, timezone

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


class Dataset(Base):
    __tablename__ = 'dataset'

    id = Column("id", INTEGER, primary_key=True)
    name = Column("name", TEXT, nullable=False)
    description = Column("description", TEXT)
    meta = Column(JSONB)
    createdAt = Column("created_at", DateTime, default=datetime.utcnow)
    updatedAt = Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
       return "<Dataset{id='%s', name='%s'}>" % (self.id, self.name)

    def as_dict(self):
        return as_dict(self)

class Image(Base):
    __tablename__ = 'image'

    id = Column("id", INTEGER, primary_key=True)
    url = Column("url", TEXT)
    md5 = Column("md5", TEXT)
    pattern = Column("pattern", Pattern)
    signature = Column(Signature)
    phash = Column(Vector(512))
    clip = Column(Vector(512))
    siglip = Column(Vector(768))
    remark = Column(TEXT)
    dataId = Column("data_id", TEXT)
    datasetId = Column("dataset_id", INTEGER)
    tags = Column("tags", ARRAY(String(64)))
    meta = Column(JSONB)
    createdAt = Column("created_at", DateTime, default=datetime.utcnow)
    updatedAt = Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
       return "<Image{id='%s', url='%s', md5='%s'}>" % (self.id, self.url, self.md5)

    def as_dict(self):
        dict_obj = as_dict(self)
        dict_obj["pattern"] = None
        dict_obj["signature"] = None
        if isinstance(dict_obj['clip'], numpy.ndarray):
            dict_obj['clip'] = [round(x, 8) for x in dict_obj['clip'].tolist()]
        if isinstance(dict_obj['siglip'], numpy.ndarray):
            dict_obj['siglip'] = [round(x, 8) for x in dict_obj['siglip'].tolist()]
        if isinstance(dict_obj['phash'], numpy.ndarray):
            dict_obj['phash'] = [round(x, 8) for x in dict_obj['phash'].tolist()]
        return dict_obj
