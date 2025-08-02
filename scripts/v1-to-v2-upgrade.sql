-- 添加新列
ALTER TABLE image ADD COLUMN siglip vector(768);
ALTER TABLE image ADD COLUMN tags text[];
ALTER TABLE image ADD COLUMN dataset_id int;
ALTER TABLE image ADD COLUMN created_at timestamp default current_timestamp;
ALTER TABLE image ADD COLUMN updated_at timestamp default current_timestamp;

-- 修改已有列的默认值（如果需要的话）
ALTER TABLE image ALTER COLUMN created_at SET DEFAULT current_timestamp;
ALTER TABLE image ALTER COLUMN updated_at SET DEFAULT current_timestamp;

-- 创建触发器自动更新 updated_at 字段（可选但推荐）
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_image_updated_at
BEFORE UPDATE ON image
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- 创建 dataset 表
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

-- 为dataset表创建触发器
CREATE TRIGGER update_dataset_updated_at BEFORE UPDATE ON dataset
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 创建默认数据集
INSERT INTO dataset (name, description, meta) 
VALUES ('默认数据集', '系统默认数据集，包含所有历史图片数据', '{"is_default": true, "created_by": "system"}'::jsonb);

-- 获取默认数据集的ID
DO $$
DECLARE
    default_dataset_id int;
BEGIN
    -- 获取刚创建的默认数据集ID
    SELECT id INTO default_dataset_id FROM dataset WHERE name = '默认数据集' LIMIT 1;
    
    -- 更新所有历史图片数据的dataset_id为默认数据集ID
    UPDATE image SET dataset_id = default_dataset_id WHERE dataset_id IS NULL;
    
    RAISE NOTICE '已创建默认数据集，ID: %, 已更新 % 条历史数据', default_dataset_id, (SELECT COUNT(*) FROM image WHERE dataset_id = default_dataset_id);
END $$;
