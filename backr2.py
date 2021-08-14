#!/usr/bin/env python3

# Copyright (c) 2021 Anthony Fadly (18fadly.anthony@gmail.com)
# This program is licensed under the GNU LGPL
# You are free to copy, modify, and redistribute the code.
# See COPYING file.

# Backr 2: Complete rewrite of backr-py (https://github.com/18fadly-anthony/backr-py)

# Imports
import os
import sys
import argparse
import socket
import hashlib
import datetime
import shutil

home = os.path.expanduser('~')
default_location = home + "/backr2-backups"
cwd = os.getcwd()

# Define general functions
def mkdirexists(dir):
    if not(os.path.isdir(dir)):
        if verbose:
            print("Creating directory " + dir)
        os.mkdir(dir)


def file_overwrite(filename, contents):
    f = open(filename, "w")
    f.write(contents)
    f.close()


def file_append(filename, contents):
    f = open(filename, "a")
    f.write(contents)
    f.close()


def file_read(filename):
    f = open(filename, "r")
    return f.read()


def tree(path):
    # Equivalent to tree command
    file_list = []
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            file_list.append(os.path.join(root, name))
        #for name in dirs:
        #    file_list.append(os.path.join(root, name))
    return file_list


def tree_dirs(path):
    file_list = []
    for root, dirs, files in os.walk(path):
        for name in dirs:
            file_list.append(os.path.join(root, name))
    return file_list


def hash_file(filename):
    if verbose:
        print("Calculating hash of " + filename)
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
        new_item.append(hash_file(i))
        table.append(new_item)
    if verbose:
        print("Created table:")
        print(table)
    return table


def read_file_to_array(filename):
    content_array = []
    with open(filename) as f:
        for line in f:
            content_array.append(line.strip('\n'))
        return(content_array)


def resolve_table(table, location, backupdir, basename, backup_number):
    for i in table:
        if not os.path.exists(location + "/" + i[1] + "/file"):
            mkdirexists(location + "/" + i[1])
            shutil.copyfile(i[0], location + "/" + i[1] + "/file")
            if verbose:
                print("Copying " + i[0] + " to " + location + "/" + i[1] + "/file")
        file_overwrite(location + "/" + i[1] + "/reference", str(backup_number))
        os.symlink(location + "/" + i[1] + "/file", backupdir + "/" + relative_path(i[0], basename))


def create_dirs(dir_list, basename, location):
    for i in dir_list:
        past_basename = False
        l = location
        for j in i.split('/'):
            if past_basename:
                l += '/' + j
            if j == basename:
                past_basename = True
        mkdirexists(l)


def relative_path(path, basename):
    past_basename = False
    l = ""
    for i in path.split('/'):
        if past_basename:
            l += '/' + i
        if i == basename:
            past_basename = True
    return l


def restore(lbh, restore_path, backup_number):
    if not os.path.exists(lbh):
        print("Specify source with --source and make sure backups of it exist")
    else:
        if os.path.exists(lbh + "/backups/" + backup_number):
            shutil.copytree(lbh + "/backups/" + backup_number, restore_path + "/backr2-restore")
            print("Restored to " + restore_path + "/backr2-restore")
        else:
            print("Error that backup does not exist")


def gc(lbh):
    if os.path.exists(lbh):
        latest = int(file_read(lbh + "/latest"))
        for i in range(1, latest):
            if os.path.exists(lbh + "/backups/" + str(i)):
                if verbose:
                    print("Deleting backup " + str(i))
                shutil.rmtree(lbh + "/backups/" + str(i))

    for i in os.listdir(lbh + "/store"):
        reference = file_read(lbh + "/store/" + i + "/reference")
        if int(reference) < latest:
            if verbose:
                print("Deleting file " + lbh + "/store/" + i)
            shutil.rmtree(lbh + "/store/" + i)


verbose = False


def main():
    global verbose
    # ArgParse
    parser = argparse.ArgumentParser(
        description = '''Backr2 backup script''',
        epilog = '''Copyright (c) 2021 Anthony Fadly (18fadly.anthony@gmail.com)'''
    )

    parser.add_argument('-l', '--location', metavar = '<path>', nargs = 1, type = str, default = [None], help = 'Location to store backup, will be ignored if .backr-location exists, defaults to ~/backr2')
    parser.add_argument('-s', '--source', metavar = '<path>', nargs = 1, type = str, default = [cwd], help = 'Source to backup, defaults to current directory')
    parser.add_argument('-r', '--restore', metavar = ('<path>', '<backup number>'), nargs = 2, type = str, default = '', help = 'restore from backup <backup number> to <path>')
    parser.add_argument('-gc', '--garbage-collect', action='store_true', help='Delete old backups')
    parser.add_argument('-d', '--default', action='store_true', help='Use default backup location: ' + default_location)
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Be verbose')

    args = parser.parse_args()

    verbose = args.verbose

    # After we're sure location exists
    source = args.source[0]
    if not os.path.exists(source):
        print("Error: source does not exist")
        exit()

    if os.path.exists(source + "/.backr2-location"):
        got_location_from_file = True
        location = file_read(source + "/.backr2-location")
    else:
        got_location_from_file = False
        if args.default:
            location = default_location
        else:
            location = args.location[0]
        if location == None:
            print("Please specify a backup location with --location or -d for default")
            exit()

    if location == default_location:
        mkdirexists(location)
    else:
        if not os.path.exists(location):
            print("Error: location does not exist")
            exit()

    # After we're sure source and location exist

    # Set some variables
    basename = os.path.basename(source)
    hostname = socket.gethostname()
    host_hash = hostname + ":" + source
    short_hash = hashlib.sha1(host_hash.encode("UTF-8")).hexdigest()[:7]
    basehash = basename + "-" + short_hash
    lbh = location + "/" + basehash


    if args.restore != '':
        restore(lbh, args.restore[0], args.restore[1])
        exit()
        # Exit after restoring to avoid running the rest of the backup script

    if args.garbage_collect:
        gc(lbh)
        exit()

    if not got_location_from_file:
        file_overwrite(source + "/.backr2-location", location)

    # Set some more variables, these ones require calling more functions
    file_list = tree(source)
    dir_list = tree_dirs(source)
    table = bootstrap_table(file_list)

    if not os.path.exists(location + "/" + basehash):
        backup_number = 1
        mkdirexists(lbh)
        mkdirexists(lbh + "/store")
        mkdirexists(lbh + "/backups")
    else:
        backup_number = int(file_read(lbh + "/latest")) + 1

    mkdirexists(lbh + "/backups/" + str(backup_number))
    create_dirs(dir_list, basename, lbh + "/backups/" + str(backup_number))
    resolve_table(table, lbh + "/store", lbh + "/backups/" + str(backup_number), basename, backup_number)
    file_overwrite(lbh + "/latest", str(backup_number))
    print("Completed backup to " + lbh + "/backups/" + str(backup_number))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('\n' + "exit")
        sys.exit(0)
