#!/usr/bin/python -i
import dbm
import sys
if len(sys.argv) != 2:
    print("Usage is ./exploredb dbfile")
    sys.exit()
print(sys.argv[1])
db = dbm.open(sys.argv[1])

print("database intialiased as db")


def print_db(db):
    for key in db.keys():
        print(key, db[key])
