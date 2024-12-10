USE `database`;

DROP TABLE EXISTS users;

DROP TABLE IF EXISTS location_activities;

DROP TABLE IF EXISTS locations CASCADE;

DROP TABLE EXISTS users;


CREATE TABLE locations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    num_ratings INT NOT NULL DEFAULT 0,
    avg_rating FLOAT NOT NULL DEFAULT 0
);

DROP TABLE IF EXISTS activities;

CREATE TABLE activities (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name TEXT NOT NULL
);

CREATE TABLE location_activities (
    location_id INT,
    activity_id INT,
    PRIMARY KEY (location_id, activity_id),
    FOREIGN KEY (location_id) REFERENCES locations(id),
    FOREIGN KEY (activity_id) REFERENCES activities(id)
);

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
);

