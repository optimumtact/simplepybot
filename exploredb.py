import shelve
import sys
import os
if len(sys.argv) != 2:
    print("Usage is ./exploredb dbfile")
    sys.exit()

db = shelve.open(sys.argv[1])
print("database intialiased as db")
print("Use print_db(db) for a printout")


def print_db(db):
    for key in db.keys():
        print(key, db[key])
