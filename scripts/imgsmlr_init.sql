
CREATE USER imgsmlr WITH PASSWORD 'imgsmlr-123456';
CREATE DATABASE imgsmlr;
GRANT ALL PRIVILEGES ON DATABASE imgsmlr TO imgsmlr;
\c imgsmlr;
GRANT ALL PRIVILEGES ON SCHEMA public TO imgsmlr;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO imgsmlr;
CREATE EXTENSION imgsmlr;
CREATE EXTENSION vector;
\c imgsmlr imgsmlr;

create table dataset (
    id serial,
    name text not null,
    description text,
    meta jsonb,
    created_at timestamp default current_timestamp,
    updated_at timestamp default current_timestamp,
    primary key(id)
);

CREATE INDEX idx_dataset_name ON dataset(name);

create table image (
    id serial,
    url text,
    md5 text,
    phash vector(512), -- phash vector
    pattern pattern, -- imgsmlr pattern
    signature signature, -- imgsmlr signature
    clip vector(512), -- CLIP vector
    siglip vector(768), -- SigLIP vector
    data_id text,
    tags text[],
    remark text,
    meta jsonb,
    dataset_id int,
    created_at timestamp default current_timestamp,
    updated_at timestamp default current_timestamp,
    primary key(id)
);

CREATE INDEX idx_image_signature ON image USING gist (signature);
CREATE INDEX idx_image_md5 ON image(md5);
CREATE INDEX idx_image_data_id ON image(data_id);
CREATE INDEX idx_image_dataset_id ON image(dataset_id);
-- Cosine distance. use query operator: <=>
CREATE INDEX idx_image_clip ON image USING hnsw (clip vector_cosine_ops)  WITH (m = 32, ef_construction = 128);
CREATE INDEX idx_image_siglip ON image USING hnsw (siglip vector_cosine_ops)  WITH (m = 32, ef_construction = 128);

-- Add tags columns
-- ALTER TABLE image ADD COLUMN tags text[];
-- ALTER TABLE image ADD COLUMN dataset_id int;
-- ALTER TABLE image ADD COLUMN siglip vector(768);

-- 创建触发器函数用于自动更新updated_at字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = current_timestamp;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为dataset表创建触发器
CREATE TRIGGER update_dataset_updated_at BEFORE UPDATE ON dataset
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 为image表创建触发器
CREATE TRIGGER update_image_updated_at BEFORE UPDATE ON image
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
