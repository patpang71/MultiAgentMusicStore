-- Migration: add PhoneNormalized column to Customer table
-- Run this once against Chinook_AutoIncrement before using get_customer_by_phone.
--
-- PhoneNormalized strips spaces, parentheses, and dashes from the Phone column
-- so that "+49 0711 2842222" and "(049) 0711-2842222" both become "+4907112842222",
-- matching the input format the tool expects: +<countrycode><digits>.
--
-- Run via CloudShell:
--   mysql -h <endpoint> -u admin -p Chinook_AutoIncrement < dbscripts/add_phone_normalized_column.sql

USE Chinook_AutoIncrement;

ALTER TABLE Customer
    ADD COLUMN IF NOT EXISTS PhoneNormalized VARCHAR(40) DEFAULT NULL;

UPDATE Customer
SET PhoneNormalized = REPLACE(
                        REPLACE(
                          REPLACE(
                            REPLACE(Phone, ' ', ''),
                          '(', ''),
                        ')', ''),
                      '-', '')
WHERE Phone IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_customer_phone_normalized
    ON Customer (PhoneNormalized);
