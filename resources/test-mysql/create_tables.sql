CREATE DATABASE IF NOT EXISTS mydatabase;
USE mydatabase;

-- Create the resinkit user first, then grant privileges
CREATE USER IF NOT EXISTS 'resinkit'@'%' IDENTIFIED BY 'resinkit_mysql_password';
GRANT SELECT, RELOAD, SHOW DATABASES, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'resinkit'@'%';
FLUSH PRIVILEGES;

-- MySQL doesn't support ENUM types as PostgreSQL does, so we'll define the ENUM directly in the tables

-- CreateTable
CREATE TABLE IF NOT EXISTS `Account` (
    `id` VARCHAR(255) NOT NULL,
    `userId` VARCHAR(255) NOT NULL,
    `type` VARCHAR(255) NOT NULL,
    `provider` VARCHAR(255) NOT NULL,
    `providerAccountId` VARCHAR(255) NOT NULL,
    `refresh_token` TEXT,
    `access_token` TEXT,
    `expires_at` INT,
    `token_type` VARCHAR(255),
    `scope` VARCHAR(255),
    `id_token` TEXT,
    `session_state` VARCHAR(255),

    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE IF NOT EXISTS `Session` (
    `id` VARCHAR(255) NOT NULL,
    `sessionToken` VARCHAR(255) NOT NULL,
    `userId` VARCHAR(255) NOT NULL,
    `expires` DATETIME(3) NOT NULL,

    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE IF NOT EXISTS `VerificationToken` (
    `identifier` VARCHAR(255) NOT NULL,
    `token` VARCHAR(255) NOT NULL,
    `expires` DATETIME(3) NOT NULL,

    PRIMARY KEY (`identifier`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE IF NOT EXISTS `User` (
    `id` VARCHAR(255) NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `email` VARCHAR(255) NOT NULL,
    `emailVerified` DATETIME(3),
    `password` VARCHAR(255),
    `image` VARCHAR(255),
    `createdAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `updatedAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    `invalid_login_attempts` INT NOT NULL DEFAULT 0,
    `lockedAt` DATETIME(3),

    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE IF NOT EXISTS `Team` (
    `id` VARCHAR(255) NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `slug` VARCHAR(255) NOT NULL,
    `domain` VARCHAR(255),
    `defaultRole` ENUM('ADMIN', 'OWNER', 'MEMBER') NOT NULL DEFAULT 'MEMBER',
    `billingId` VARCHAR(255),
    `billingProvider` VARCHAR(255),
    `createdAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `updatedAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),

    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE IF NOT EXISTS `TeamMember` (
    `id` VARCHAR(255) NOT NULL,
    `teamId` VARCHAR(255) NOT NULL,
    `userId` VARCHAR(255) NOT NULL,
    `role` ENUM('ADMIN', 'OWNER', 'MEMBER') NOT NULL DEFAULT 'MEMBER',
    `createdAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `updatedAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),

    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE IF NOT EXISTS `Invitation` (
    `id` VARCHAR(255) NOT NULL,
    `teamId` VARCHAR(255) NOT NULL,
    `email` VARCHAR(255),
    `role` ENUM('ADMIN', 'OWNER', 'MEMBER') NOT NULL DEFAULT 'MEMBER',
    `token` VARCHAR(255) NOT NULL,
    `expires` DATETIME(3) NOT NULL,
    `invitedBy` VARCHAR(255) NOT NULL,
    `createdAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `updatedAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    `sentViaEmail` BOOLEAN NOT NULL DEFAULT true,
    `allowedDomains` JSON,

    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE IF NOT EXISTS `PasswordReset` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `email` VARCHAR(255) NOT NULL,
    `token` VARCHAR(255) NOT NULL,
    `createdAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `updatedAt` DATETIME(3) NOT NULL ON UPDATE CURRENT_TIMESTAMP(3),
    `expiresAt` DATETIME(3) NOT NULL,

    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE IF NOT EXISTS `ApiKey` (
    `id` VARCHAR(255) NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `teamId` VARCHAR(255) NOT NULL,
    `hashedKey` VARCHAR(255) NOT NULL,
    `createdAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `updatedAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    `expiresAt` DATETIME(3),
    `lastUsedAt` DATETIME(3),

    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE IF NOT EXISTS `Subscription` (
    `id` VARCHAR(255) NOT NULL,
    `customerId` VARCHAR(255) NOT NULL,
    `priceId` VARCHAR(255) NOT NULL,
    `active` BOOLEAN NOT NULL DEFAULT false,
    `startDate` DATETIME(3) NOT NULL,
    `endDate` DATETIME(3) NOT NULL,
    `cancelAt` DATETIME(3),
    `createdAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `updatedAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),

    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE IF NOT EXISTS `Service` (
    `id` VARCHAR(255) NOT NULL,
    `description` TEXT NOT NULL,
    `features` JSON,
    `image` VARCHAR(255) NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `created` DATETIME(3) NOT NULL,
    `createdAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    `updatedAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),

    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE IF NOT EXISTS `Price` (
    `id` VARCHAR(255) NOT NULL,
    `billingScheme` VARCHAR(255) NOT NULL,
    `currency` VARCHAR(255) NOT NULL,
    `serviceId` VARCHAR(255) NOT NULL,
    `amount` INT,
    `metadata` JSON NOT NULL,
    `type` VARCHAR(255) NOT NULL,
    `created` DATETIME(3) NOT NULL,

    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE IF NOT EXISTS `jackson_store` (
    `key` VARCHAR(500) NOT NULL,
    `value` TEXT NOT NULL,
    `iv` VARCHAR(64),
    `tag` VARCHAR(64),
    `createdAt` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `modifiedAt` DATETIME(6),
    `namespace` VARCHAR(64),

    PRIMARY KEY (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE IF NOT EXISTS `jackson_index` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `key` VARCHAR(500) NOT NULL,
    `storeKey` VARCHAR(500) NOT NULL,

    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE IF NOT EXISTS `jackson_ttl` (
    `key` VARCHAR(500) NOT NULL,
    `expiresAt` BIGINT NOT NULL,

    PRIMARY KEY (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE IF NOT EXISTS `t_data_connection_config` (
    `id` VARCHAR(255) NOT NULL,
    `ownerTeamId` VARCHAR(255),
    `name` VARCHAR(255) NOT NULL,
    `type` VARCHAR(255) NOT NULL,
    `details` JSON NOT NULL,
    `createdBy` VARCHAR(255),
    `updatedBy` VARCHAR(255),
    `updatedAt` DATETIME(3) NOT NULL,

    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE IF NOT EXISTS `t_flink_cdc_config` (
    `id` VARCHAR(255) NOT NULL,
    `ownerTeamId` VARCHAR(255),
    `name` VARCHAR(255) NOT NULL,
    `sourceConnId` VARCHAR(255) NOT NULL,
    `sourceTables` VARCHAR(255) NOT NULL,
    `sinkConnId` VARCHAR(255) NOT NULL,
    `transform` JSON,
    `route` JSON,
    `pipeline` JSON,
    `createdBy` VARCHAR(255),
    `updatedBy` VARCHAR(255),
    `updatedAt` DATETIME(3) NOT NULL,

    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
