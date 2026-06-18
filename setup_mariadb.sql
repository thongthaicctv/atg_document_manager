CREATE DATABASE IF NOT EXISTS `atg_document_system`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'atg_admin'@'localhost'
  IDENTIFIED BY 'atg_123456';

CREATE USER IF NOT EXISTS 'atg_admin'@'127.0.0.1'
  IDENTIFIED BY 'atg_123456';

ALTER USER 'atg_admin'@'localhost'
  IDENTIFIED BY 'atg_123456';

ALTER USER 'atg_admin'@'127.0.0.1'
  IDENTIFIED BY 'atg_123456';

GRANT ALL PRIVILEGES ON `atg_document_system`.*
  TO 'atg_admin'@'localhost';

GRANT ALL PRIVILEGES ON `atg_document_system`.*
  TO 'atg_admin'@'127.0.0.1';

FLUSH PRIVILEGES;
