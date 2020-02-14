-- create the database
create database db_trashdump;
use db_trashdump;

CREATE TABLE `post` (
  `id` varchar(45) NOT NULL,
  `text` mediumtext,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE `category` (
  `user` varchar(45) NOT NULL,
  `post_id` varchar(45) NOT NULL,
  `created_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `duration_seconds` decimal(12,6) DEFAULT NULL,
  PRIMARY KEY (`user`,`post_id`),
  KEY `fk_category_post1_idx` (`post_id`),
  CONSTRAINT `fk_category_post1` FOREIGN KEY (`post_id`) REFERENCES `post` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `phase` (
  `id` int(11) NOT NULL,
  `name` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `post_has_phase` (
  `post_id` varchar(45) NOT NULL,
  `phase_id` int(11) NOT NULL,
  PRIMARY KEY (`post_id`,`phase_id`),
  KEY `fk_post_has_phase_phase1_idx` (`phase_id`),
  KEY `fk_post_has_phase_post1_idx` (`post_id`),
  CONSTRAINT `fk_post_has_phase_phase1` FOREIGN KEY (`phase_id`) REFERENCES `phase` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_post_has_phase_post1` FOREIGN KEY (`post_id`) REFERENCES `post` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `skip` (
  `user` varchar(45) NOT NULL,
  `post_id` varchar(45) NOT NULL,
  `created_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `duration_seconds` decimal(12,6) DEFAULT NULL,
  PRIMARY KEY (`user`,`post_id`,`created_time`),
  KEY `fk_skip_post1_idx` (`post_id`),
  CONSTRAINT `fk_skip_post1` FOREIGN KEY (`post_id`) REFERENCES `post` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `category_name` (
  `id` int(11) NOT NULL,
  `name` mediumtext,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `category_has_category_name` (
  `user` varchar(45) NOT NULL,
  `post_id` varchar(45) NOT NULL,
  `category_name_id` int(11) NOT NULL,
  PRIMARY KEY (`user`,`post_id`,`category_name_id`),
  KEY `fk_category_has_category_name_category_name1_idx` (`category_name_id`),
  KEY `fk_category_has_category_name_category1_idx` (`user`,`post_id`),
  CONSTRAINT `fk_category_has_category_name_category1` FOREIGN KEY (`user`, `post_id`) REFERENCES `category` (`user`, `post_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_category_has_category_name_category_name1` FOREIGN KEY (`category_name_id`) REFERENCES `category_name` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
