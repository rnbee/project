
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(20) NOT NULL UNIQUE
);

INSERT INTO categories (category_name) VALUES ('clothes');
INSERT INTO categories (category_name) VALUES ('electronics');
INSERT INTO categories (category_name) VALUES ('other');


CREATE TABLE IF NOT EXISTS parcels (
    id INT AUTO_INCREMENT PRIMARY KEY,
    parcel_name VARCHAR(20) NOT NULL UNIQUE,
    weight FLOAT NOT NULL,
    cost INT NOT NULL,
    parcel_category INT NOT NULL,
    delivery_cost FLOAT DEFAULT NULL,
    FOREIGN KEY (parcel_category) REFERENCES categories(id),
    session_id VARCHAR(36) NOT NULL
);

CREATE INDEX hash_index on parcels (session_id) USING HASH;