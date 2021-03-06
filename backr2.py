#!/usr/bin/env python3

# Copyright (c) 2020 Anthony Fadly (18fadly.anthony@gmail.com)
# This program is licensed under the Apache License 2.0
# You are free to copy, modify, and redistribute the code.
# See LICENSE file.

# Backr 2: Complete rewrite of backr-py

# Imports
import os
import argparse
import socket
import hashlib

home = os.path.expanduser('~')
default_location = home + "/backr2"
cwd = os.getcwd()

# Define general functions
def mkdirexists(dir):
    if not(os.path.isdir(dir)):
        os.mkdir(dir)


def file_overwrite(filename, contents):
    f = open(filename, "w")
    f.write(contents)
    f.close()


def tree(path):
    # Equivalent to tree command
    file_list = []
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            file_list.append(os.path.join(root, name))
        for name in dirs:
            file_list.append(os.path.join(root, name))
    return file_list


def hash_file(filename):
    BLOCKSIZE = 65536
    hasher = hashlib.sha1()
    with open(filename, 'rb') as afile:
        buf = afile.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(BLOCKSIZE)
    return hasher.hexdigest()


def bootstrap_table(file_list):
    table = []
    for i in file_list:
        new_item = []
        new_item.append(i)
        if os.path.isfile(i):
            new_item.append("file")
            new_item.append(hash_file(i))
            new_item.append("1")
        elif os.path.isdir(i):
            new_item.append("dir")
        print(new_item)


def main():

    # ArgParse
    parser = argparse.ArgumentParser(
        description = '''placeholder''',
        epilog = '''placeholder'''
    )

    parser.add_argument('--location', metavar = '<path>', nargs = 1, type = str, default = [default_location], help = 'Location to store backup, will be ignored if .backr-location exists, defaults to ~/backrs')
    parser.add_argument('--source', metavar = '<path>', nargs = 1, type = str, default = [cwd], help = 'Source to backup, defaults to current directory')

    args = parser.parse_args()

    location = args.location[0]
    if location == default_location:
        mkdirexists(location)
    else:
        if not os.path.exists(location):
            print("Error: location does not exist")
            exit()

    # After we're sure location exists
    source = args.source[0]
    if not os.path.exists(source):
        print("Error: source does not exist")
        exit()

    # After we're sure source and  location exist

    basename = os.path.basename(source)
    hostname = socket.gethostname()
    host_hash = hostname + ":" + source
    short_hash = hashlib.sha1(host_hash.encode("UTF-8")).hexdigest()[:7]
    basehash = basename + "-" + short_hash

    if not os.path.exists(location + "/" + basehash):
        # Scenario for initial backup
        backup_number = 1
        mkdirexists(location + "/" + basehash)
        mkdirexists(location + "/" + basehash + "/store")
        mkdirexists(location + "/" + basehash + "/backups")
        mkdirexists(location + "/" + basehash + "/backups/" + str(backup_number))
        file_list = tree(source)
        bootstrap_table(file_list)
    else:
        # TODO write scenario for after first backup
        pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('\n' + "exit")
        sys.exit(0)
