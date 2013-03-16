#!/usr/bin/python2 -i

import shelve
import sys
import os
if len(sys.argv) != 2:
    print("Usage is ./exploredb dbfile")
    sys.exit()

print(os.getcwd())
print(sys.argv)
print(sys.argv[1])
db = shelve.open('BOTDB')

print("database intialiased as db")


def print_db(db):
    for key in db.keys():
        print(key, db[key])
