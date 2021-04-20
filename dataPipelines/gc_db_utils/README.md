# ORM & DB Utils

Utilities for working with databases

## General Structure
- `./<db-name-shorthand>` - directory with modules for interacting with certain database.
- `./<db...>/models.py` - sqlalchemy ORM models for given db
- `./<db...>/schemas.py` - sqlalchemy schemas for given db
- `./<db...>/utils.py` - set of utils for retrieving/setting entities for a given db.
- `./scripts` - cmdline scripts

## Table Migrations
Scripts for orchestrating table migrations (such as when altering table schema) belong in relevant 
`./<db-name>/migrations` dir tree. General idea is to use `../migrations/scripts` for standalone migration
script wrappers and `../migrations/sql` for any associated sql files. `./<db-name>/sql/` should always have
the latest schema definitions. 