
CREATE USER imgsmlr WITH PASSWORD 'imgsmlr-123456';
CREATE DATABASE imgsmlr;
GRANT ALL PRIVILEGES ON DATABASE imgsmlr TO imgsmlr;
\c imgsmlr;
create extension imgsmlr;
\c imgsmlr imgsmlr;

create table image (
    id serial,
    url text,
    md5 text,
    pattern pattern,
    signature signature,
    data_id text,
    remark text,
    meta jsonb,
    primary key(id)
);

CREATE INDEX idx_image_signature ON image USING gist (signature);
CREATE INDEX idx_image_md5 ON image(md5);
CREATE INDEX idx_image_data_id ON image(data_id);
