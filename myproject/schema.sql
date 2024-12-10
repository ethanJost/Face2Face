USE `database`;

ALTER TABLE activities MODIFY name VARCHAR(255) NOT NULL;
CREATE INDEX idx_activities_name ON activities(name);
