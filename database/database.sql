CREATE DATABASE employee_portal;

USE employee_portal;

CREATE TABLE users(

id INT AUTO_INCREMENT PRIMARY KEY,

employee_id VARCHAR(50),

password VARCHAR(50),

role VARCHAR(20),

department VARCHAR(100)

);

INSERT INTO users
(employee_id,password,role,department)

VALUES

('ADMIN001','1234','ADMIN','ALL'),

('HOD001','1234','HOD','IT'),

('EMP001','1234','STAFF','IT');