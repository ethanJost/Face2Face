USE `database`;


DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS location_activities;
DROP TABLE IF EXISTS activities;
DROP TABLE IF EXISTS locations;

CREATE TABLE locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    num_ratings INT NOT NULL DEFAULT 0,
    avg_rating FLOAT NOT NULL DEFAULT 0
);

CREATE TABLE activities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE location_activities (
    location_id INT,
    activity_id INT,
    PRIMARY KEY (location_id, activity_id),
    FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE,
    FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
);

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
);

ALTER TABLE activities MODIFY name VARCHAR(255) NOT NULL;
CREATE INDEX idx_activities_name ON activities(name);
