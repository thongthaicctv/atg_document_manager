CREATE DATABASE IF NOT EXISTS `atg_document_system`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'atg_doc_user'@'localhost'
  IDENTIFIED BY 'atg_password';

CREATE USER IF NOT EXISTS 'atg_doc_user'@'127.0.0.1'
  IDENTIFIED BY 'atg_password';

ALTER USER 'atg_doc_user'@'localhost'
  IDENTIFIED BY 'atg_password';

ALTER USER 'atg_doc_user'@'127.0.0.1'
  IDENTIFIED BY 'atg_password';

GRANT ALL PRIVILEGES ON `atg_document_system`.*
  TO 'atg_doc_user'@'localhost';

GRANT ALL PRIVILEGES ON `atg_document_system`.*
  TO 'atg_doc_user'@'127.0.0.1';

FLUSH PRIVILEGES;
