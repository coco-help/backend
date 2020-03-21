ALTER TABLE helper
ADD COLUMN verified BOOLEAN;
UPDATE helper SET verified = true;

ALTER TABLE helper
ALTER COLUMN verified SET NOT NULL;
