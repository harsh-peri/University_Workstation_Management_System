-- =======================================
-- UNIVERSITY WORKSTATION MANAGEMENT SYSTEM
-- COMPLETE SQL SCHEMA + FUNCTIONS + TRIGGERS + PROCEDURES + SAMPLE DATA
-- =======================================

DROP DATABASE IF EXISTS university_workstation;
CREATE DATABASE university_workstation;
USE university_workstation;

-- =======================================
-- TABLES
-- =======================================

CREATE TABLE campus (
    campus_id INT PRIMARY KEY,
    campus_name VARCHAR(50) NOT NULL,
    location VARCHAR(50) NOT NULL,
    contact BIGINT
);

CREATE TABLE block (
    block_id INT PRIMARY KEY,
    block_name VARCHAR(50) NOT NULL,
    no_of_buildings INT NOT NULL
);

CREATE TABLE building (
    building_id INT PRIMARY KEY,
    build_name VARCHAR(50) NOT NULL,
    no_of_floor INT NOT NULL
);

CREATE TABLE department (
    dept_id INT PRIMARY KEY,
    dept_hod_id INT,
    dept_name VARCHAR(60) NOT NULL
);

CREATE TABLE floor (
    floor_no INT PRIMARY KEY,
    floor_name VARCHAR(50) NOT NULL,
    no_of_rooms INT NOT NULL,
    dept_id INT NOT NULL,
    building_id INT NOT NULL,
    block_id INT NOT NULL,
    campus_id INT NOT NULL
);

CREATE TABLE room (
    room_no INT PRIMARY KEY,
    location VARCHAR(50) NOT NULL,
    type VARCHAR(50),
    is_allotted BIT(1) NOT NULL,
    floor_no INT NOT NULL,
    building_id INT NOT NULL,
    block_id INT NOT NULL,
    campus_id INT NOT NULL
);

CREATE TABLE faculty (
    faculty_id INT PRIMARY KEY,
    faculty_name VARCHAR(60) NOT NULL,
    date_of_join DATE NOT NULL,
    post VARCHAR(50) NOT NULL,
    contact BIGINT,
    room_no INT,
    dept_id INT
);

-- =======================================
-- FOREIGN KEYS
-- =======================================

ALTER TABLE block
    ADD COLUMN campus_id INT,
    ADD CONSTRAINT fk_block_campus
    FOREIGN KEY (campus_id) REFERENCES campus(campus_id);

ALTER TABLE building
    ADD COLUMN block_id INT,
    ADD COLUMN campus_id INT,
    ADD CONSTRAINT fk_building_block FOREIGN KEY (block_id) REFERENCES block(block_id),
    ADD CONSTRAINT fk_building_campus FOREIGN KEY (campus_id) REFERENCES campus(campus_id);

ALTER TABLE floor
    ADD CONSTRAINT fk_floor_building FOREIGN KEY (building_id) REFERENCES building(building_id),
    ADD CONSTRAINT fk_floor_block FOREIGN KEY (block_id) REFERENCES block(block_id),
    ADD CONSTRAINT fk_floor_campus FOREIGN KEY (campus_id) REFERENCES campus(campus_id),
    ADD CONSTRAINT fk_floor_dept FOREIGN KEY (dept_id) REFERENCES department(dept_id);

ALTER TABLE room
    ADD CONSTRAINT fk_room_floor FOREIGN KEY (floor_no) REFERENCES floor(floor_no),
    ADD CONSTRAINT fk_room_building FOREIGN KEY (building_id) REFERENCES building(building_id),
    ADD CONSTRAINT fk_room_block FOREIGN KEY (block_id) REFERENCES block(block_id),
    ADD CONSTRAINT fk_room_campus FOREIGN KEY (campus_id) REFERENCES campus(campus_id);

ALTER TABLE department
    ADD CONSTRAINT fk_dept_hod FOREIGN KEY (dept_hod_id) REFERENCES faculty(faculty_id);

ALTER TABLE faculty
    ADD CONSTRAINT fk_faculty_room FOREIGN KEY (room_no) REFERENCES room(room_no),
    ADD CONSTRAINT fk_faculty_dept FOREIGN KEY (dept_id) REFERENCES department(dept_id);

-- =======================================
-- SAMPLE DATA
-- =======================================

INSERT INTO campus VALUES
(1, 'RR', 'Banashankari', 9112345678),
(2, 'EC', 'Electronic City', 9123456789);

INSERT INTO block VALUES
(1, 'RR_Block_A', 3, 1),
(2, 'RR_Block_B', 2, 1),
(3, 'EC_Block_A', 4, 2),
(4, 'EC_Block_B', 3, 2),
(5, 'EC_Block_C', 2, 2);

INSERT INTO building VALUES
(1, 'RR_A_Building1', 4, 1, 1),
(2, 'RR_B_Building1', 3, 2, 1),
(3, 'EC_A_Building1', 5, 3, 2),
(4, 'EC_B_Building1', 4, 4, 2),
(5, 'EC_C_Building1', 3, 5, 2);

INSERT INTO department VALUES
(1, NULL, 'CSE'),
(2, NULL, 'ECE'),
(3, NULL, 'MECH'),
(4, NULL, 'AIML'),
(5, NULL, 'PHARMA'),
(6, NULL, 'NURSING'),
(7, NULL, 'MBBS');

INSERT INTO floor VALUES
(1, 'Ground Floor', 10, 1, 1, 1, 1),
(2, 'First Floor', 8, 2, 2, 2, 1),
(3, 'Second Floor', 12, 3, 3, 3, 2),
(4, 'Third Floor', 10, 4, 4, 2, 4),
(5, 'Fourth Floor', 6, 5, 5, 5, 2);

INSERT INTO room VALUES
(101, 'RR-A1', 'Lab', b'1', 1, 1, 1, 1),
(102, 'RR-B1', 'Lecture', b'1', 2, 2, 2, 1),
(201, 'EC-A1', 'Office', b'1', 3, 3, 3, 2),
(202, 'EC-B1', 'Lecture', b'0', 4, 4, 4, 2),
(203, 'EC-C1', 'Lab', b'1', 5, 5, 5, 2);

INSERT INTO faculty VALUES
(1, 'Dr. Asha Kumar', '2015-06-10', 'Professor', 9876543210, 101, 1),
(2, 'Dr. Ravi Menon', '2017-09-15', 'Associate Professor', 9876543211, 102, 2),
(3, 'Dr. Priya Nair', '2018-02-20', 'Professor', 9876543212, 201, 3),
(4, 'Dr. Kiran Rao', '2020-01-05', 'Assistant Professor', 9876543213, 202, 4),
(5, 'Dr. Neha Patil', '2019-03-25', 'Professor', 9876543214, 203, 5);

UPDATE department SET dept_hod_id = 1 WHERE dept_id = 1;
UPDATE department SET dept_hod_id = 2 WHERE dept_id = 2;
UPDATE department SET dept_hod_id = 3 WHERE dept_id = 3;
UPDATE department SET dept_hod_id = 4 WHERE dept_id = 4;
UPDATE department SET dept_hod_id = 5 WHERE dept_id = 5;

-- =======================================
-- FUNCTIONS
-- =======================================

DELIMITER $$

CREATE FUNCTION get_block_path(block_id_input INT)
RETURNS VARCHAR(150)
DETERMINISTIC
BEGIN
    DECLARE blockName, campusName VARCHAR(50);
    SELECT bl.block_name, c.campus_name
    INTO blockName, campusName
    FROM block bl
    JOIN campus c ON bl.campus_id = c.campus_id
    WHERE bl.block_id = block_id_input;

    RETURN CONCAT(campusName, ' > ', blockName);
END$$

CREATE FUNCTION get_building_path(building_id_input INT)
RETURNS VARCHAR(200)
DETERMINISTIC
BEGIN
    DECLARE buildName, blockName, campusName VARCHAR(50);
    SELECT b.build_name, bl.block_name, c.campus_name
    INTO buildName, blockName, campusName
    FROM building b
    JOIN block bl ON b.block_id = bl.block_id
    JOIN campus c ON b.campus_id = c.campus_id
    WHERE b.building_id = building_id_input;

    RETURN CONCAT(campusName, ' > ', blockName, ' > ', buildName);
END$$

CREATE FUNCTION get_floor_path(floor_no_input INT)
RETURNS VARCHAR(250)
DETERMINISTIC
BEGIN
    DECLARE floorName, buildName, blockName, campusName VARCHAR(50);
    SELECT f.floor_name, b.build_name, bl.block_name, c.campus_name
    INTO floorName, buildName, blockName, campusName
    FROM floor f
    JOIN building b ON f.building_id = b.building_id
    JOIN block bl ON f.block_id = bl.block_id
    JOIN campus c ON f.campus_id = c.campus_id
    WHERE f.floor_no = floor_no_input;

    RETURN CONCAT(campusName, ' > ', blockName, ' > ', buildName, ' > ', floorName);
END$$

CREATE FUNCTION get_room_path(room_no_input INT)
RETURNS VARCHAR(300)
DETERMINISTIC
BEGIN
    DECLARE roomLabel, floorName, buildName, blockName, campusName VARCHAR(50);
    SELECT CONCAT('Room ', r.room_no), f.floor_name, b.build_name, bl.block_name, c.campus_name
    INTO roomLabel, floorName, buildName, blockName, campusName
    FROM room r
    JOIN floor f ON r.floor_no = f.floor_no
    JOIN building b ON r.building_id = b.building_id
    JOIN block bl ON r.block_id = bl.block_id
    JOIN campus c ON r.campus_id = c.campus_id
    WHERE r.room_no = room_no_input;

    RETURN CONCAT(campusName, ' > ', blockName, ' > ', buildName, ' > ', floorName, ' > ', roomLabel);
END$$

CREATE FUNCTION faculty_count(deptId INT)
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE countVal INT;
    SELECT COUNT(*) INTO countVal FROM faculty WHERE dept_id = deptId;
    RETURN countVal;
END$$

DELIMITER ;

-- =======================================
-- TRIGGERS
-- =======================================

CREATE TABLE faculty_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    faculty_id INT,
    old_room INT,
    new_room INT,
    change_date DATETIME
);

DELIMITER $$

CREATE TRIGGER trg_faculty_delete
AFTER DELETE ON faculty
FOR EACH ROW
BEGIN
    UPDATE department SET dept_hod_id = NULL
    WHERE dept_hod_id = OLD.faculty_id;
END$$

CREATE TRIGGER trg_faculty_room_check
BEFORE INSERT ON faculty
FOR EACH ROW
BEGIN
    IF NEW.room_no IS NOT NULL AND
       (SELECT COUNT(*) FROM room WHERE room_no = NEW.room_no) = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Invalid Room Number for Faculty';
    END IF;
END$$

CREATE TRIGGER trg_faculty_room_update
AFTER UPDATE ON faculty
FOR EACH ROW
BEGIN
    IF OLD.room_no <> NEW.room_no THEN
        INSERT INTO faculty_log(faculty_id, old_room, new_room, change_date)
        VALUES (NEW.faculty_id, OLD.room_no, NEW.room_no, NOW());
    END IF;
END$$

DELIMITER ;

-- =======================================
-- STORED PROCEDURES
-- =======================================

DELIMITER $$

CREATE PROCEDURE get_faculty_details(IN fac_id INT)
BEGIN
    SELECT f.faculty_id, f.faculty_name, f.post, f.date_of_join,
           d.dept_name, r.location AS room_location,
           c.campus_name, c.location AS campus_location
    FROM faculty f
    LEFT JOIN department d ON f.dept_id = d.dept_id
    LEFT JOIN room r ON f.room_no = r.room_no
    LEFT JOIN campus c ON r.campus_id = c.campus_id
    WHERE f.faculty_id = fac_id;
END$$

CREATE PROCEDURE add_faculty(
    IN f_name VARCHAR(60),
    IN doj DATE,
    IN post VARCHAR(50),
    IN contact BIGINT,
    IN roomNum INT,
    IN deptId INT
)
BEGIN
    IF (SELECT COUNT(*) FROM department WHERE dept_id = deptId) = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Department does not exist';

    ELSEIF (SELECT COUNT(*) FROM room WHERE room_no = roomNum) = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Room does not exist';

    ELSE
        INSERT INTO faculty (faculty_name, date_of_join, post, contact, room_no, dept_id)
        VALUES (f_name, doj, post, contact, roomNum, deptId);
    END IF;
END$$

CREATE PROCEDURE get_rooms_by_campus(IN campusName VARCHAR(50))
BEGIN
    SELECT r.room_no, r.type, r.is_allotted, f.floor_name, b.build_name, c.campus_name
    FROM room r
    JOIN floor f ON r.floor_no = f.floor_no
    JOIN building b ON r.building_id = b.building_id
    JOIN campus c ON r.campus_id = c.campus_id
    WHERE c.campus_name = campusName;
END$$

DELIMITER ;

-- =======================================
-- END OF FILE
-- =======================================
