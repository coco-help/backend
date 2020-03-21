ALTER TABLE helper
ADD COLUMN is_active BOOLEAN;

UPDATE helper SET is_active = true;

ALTER TABLE helper
ALTER COLUMN is_active SET NOT NULL;
