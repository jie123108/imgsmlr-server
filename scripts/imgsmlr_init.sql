
CREATE USER imgsmlr WITH PASSWORD 'imgsmlr-123456';
CREATE DATABASE imgsmlr;
GRANT ALL PRIVILEGES ON DATABASE imgsmlr TO imgsmlr;
\c imgsmlr;
GRANT ALL PRIVILEGES ON SCHEMA public TO imgsmlr;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO imgsmlr;
CREATE EXTENSION imgsmlr;
CREATE EXTENSION vector;
\c imgsmlr imgsmlr;

create table image (
    id serial,
    url text,
    md5 text,
    phash vector(512), -- phash vector
    pattern pattern, -- imgsmlr pattern
    signature signature, -- imgsmlr signature
    clip vector(512), -- CLIP vector
    data_id text,
    remark text,
    meta jsonb,
    primary key(id)
);

CREATE INDEX idx_image_signature ON image USING gist (signature);
CREATE INDEX idx_image_md5 ON image(md5);
CREATE INDEX idx_image_data_id ON image(data_id);
-- Cosine distance. use query operator: <=>
CREATE INDEX idx_image_clip ON image USING hnsw (clip vector_cosine_ops)  WITH (m = 16, ef_construction = 64);

