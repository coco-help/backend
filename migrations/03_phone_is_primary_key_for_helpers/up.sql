ALTER TABLE helper
DROP CONSTRAINT helper_pkey,
ADD CONSTRAINT helper_pkey PRIMARY KEY (phone),
DROP COLUMN id;
