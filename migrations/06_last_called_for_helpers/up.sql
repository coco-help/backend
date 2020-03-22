ALTER TABLE helper
ADD COLUMN last_called TIMESTAMP;

UPDATE helper
SET last_called = current_timestamp;

ALTER TABLE helper
ALTER COLUMN last_called SET NOT NULL;
