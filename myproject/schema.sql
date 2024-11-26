USE `database`;

DROP TABLE IF EXISTS location_activities;

DROP TABLE IF EXISTS locations CASCADE;

CREATE TABLE locations (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    address TEXT
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
