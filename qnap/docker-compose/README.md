# rdbs.yml

This docker-compose script defines the relational database containers that run
on QNAP. The intent here is for the QNAP NAS to serve as a general-purpose
database server for non-intense database loads. It has the benefit of redundant
storage by virtue of its RAID-5 setup and so the database payloads are safer
there. It is also a more lightly-used resource with much more storage while
still having a dual-core CPU (Intel Celeron) and 8 GB of RAM.

## Migrating existing PostgreSQL databases

The principal challenge in utilizing the QNAP device as my primary database
server was migrating the database server I had been using (one of my Linux
workstations), since it had a variety of logins with a minimal set of
permissions for each database.

It turns out that the `pg_dumpall` utility will capture the full contents of the
server including:

* database schemas
* user accounts with credentials
* all of the data

To execute the migration, I needed the following commands:

### Create the backup file

This command is run from the machine where the database I want migrated is
hosted using the server-admin account that ships with most PostgreSQL
installations (postgres).

```bash
pg_dumpall -h localhost -U postgres -f full-dump.out
```

### Restore the backup file to the QNAP server

This command restores everything extracted from the server on my Linux
workstation and copies it to the PostgreSQL container running on Container
Station in my QNAP.

```bash
psql -U postgres -f full-dump.out -h 192.168.1.55
```

Following this operation, all of the databases, their data, users, and assigned
roles were available in the newly-restored database hosted on QNAP. The services
leveraging these databases were migrated just as easily.  Success!
