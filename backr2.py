#!/usr/bin/env python3

# Copyright (c) 2021 Anthony Fadly (18fadly.anthony@gmail.com)
# This program is licensed under the GNU LGPL
# You are free to copy, modify, and redistribute the code.
# See COPYING file.

# Backr 2: Complete rewrite of backr-py (https://github.com/18fadly-anthony/backr-py)

# Imports
import os
import sys
import math
import socket
import shutil
import tarfile
import hashlib
import argparse
import mimetypes
from typing import Iterator, List

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


class FileTable:
    class Entry:
        def __init__(self, file_name: str, file_hash: str):
            self.file_name: str = file_name
            self.file_hash: str = file_hash

        def __str__(self) -> str:
            """
            Converts this Entry to a string.

            Convert this Entry to a string of the format `<file name> (sha-1: <file hash>)`
            """
            return "%s (sha-1: %s)" % (self.file_name, self.file_hash)

    def __init__(self, file_list: List[str] = []):
        self.__file_list: List[FileTable.Entry] = []
        for i in file_list:
            self.__file_list.append(FileTable.Entry(i, hash_file(i)))
        if verbose:
            print("Created table:")
            print(self)

    def __str__(self) -> str:
        return str(self.__file_list)

    def __iter__(self) -> Iterator[Entry]:
        return self.__file_list.__iter__()


def decide_to_compress(filename):
    compressed_formats = ['audio', 'image', 'application', 'video']
    uncompressed_formats = ['text']
    mime = mimetypes.guess_type(filename)
    shortmime = str(mime[0]).split('/')[0]
    if shortmime in compressed_formats:
        return False
    elif shortmime in uncompressed_formats:
        return True
    else:
        return decide_by_entropy(filename)


# Compress files only if they would compress to 90% or less of their original size
# This code was adapted from Kenneth Hartman who posted the original in Python 2
# https://kennethghartman.com/calculate-file-entropy/
def decide_by_entropy(filename):
    compression_threshold = 90
    f = open(filename, "rb")
    byteArr = list(f.read())
    f.close()
    fileSize = len(byteArr)
    # Prevent divide by zero error
    if fileSize == 0:
        return False
    freqList = []
    for b in range(256):
        ctr = 0
        for byte in byteArr:
            if byte == b:
                ctr += 1
        freqList.append(float(ctr) / fileSize)
    ent = 0.0
    for freq in freqList:
        if freq > 0:
            ent = ent + freq * math.log(freq, 2)
    ent = -ent
    compression_ratio = (((ent * fileSize) / 8) / fileSize) * 100
    return compression_ratio <= compression_threshold


def resolve_table(table: FileTable, lbh, backupdir, basename, backup_number, compression, smart_compression):
    location = lbh + "/store"
    for i in table:
        mkdirexists(location + "/" + i.file_hash)
        if smart_compression:
            compression = decide_to_compress(i.file_name)
        if compression:
            file_overwrite(location + "/" + i.file_hash + "/reference_tar", str(backup_number))
            if not os.path.exists(location + "/" + i.file_hash + "/file.tar.gz"):
                compress(i.file_name, location + "/" + i.file_hash + "/file.tar.gz")
                if verbose:
                    print("Compressing " + i.file_name + " to " + location + "/" + i.file_hash + "/file.tar.gz")
        else:
            file_overwrite(location + "/" + i.file_hash + "/reference", str(backup_number))
            if not os.path.exists(location + "/" + i.file_hash + "/file"):
                shutil.copyfile(i.file_name, location + "/" + i.file_hash + "/file")
            if verbose:
                print("Copying " + i.file_name + " to " + location + "/" + i.file_hash + "/file")
        symlink_location = "../../"
        for j in range(relative_depth(backupdir + relative_path(i.file_name, basename), lbh) - 4):
            symlink_location += "../"
        if compression:
            symlink_location += "store/" + i.file_hash + "/file.tar.gz"
            os.symlink(symlink_location, backupdir + relative_path(i.file_name, basename) + ".tar.gz")
        else:
            symlink_location += "store/" + i.file_hash + "/file"
            os.symlink(symlink_location, backupdir + relative_path(i.file_name, basename))


def relative_depth(path1, path2):
    return len(relative_path(path1, os.path.basename(path2)).split('/'))


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
                print("Deleting backup " + str(i))
                shutil.rmtree(lbh + "/backups/" + str(i))

    for i in os.listdir(lbh + "/store"):
        if os.path.exists(lbh + "/store/" + i + "/reference"):
            reference = file_read(lbh + "/store/" + i + "/reference")
            if int(reference) < latest:
                if os.path.exists(lbh + "/store/" + i + "/file"):
                    if verbose:
                        print("Deleting file " + lbh + "/store/" + i + "/file")
                    os.remove(lbh + "/store/" + i + "/file")
                    os.remove(lbh + "/store/" + i + "/reference")
                if not os.path.exists(lbh + "/store/" + i + "/file.tar.gz"):
                    shutil.rmtree(lbh + "/store/" + i)
        if os.path.exists(lbh + "/store/" + i + "/reference_tar"):
            reference_tar = file_read(lbh + "/store/" + i + "/reference_tar")
            if int(reference_tar) < latest:
                if os.path.exists(lbh + "/store/" + i + "/file.tar.gz"):
                    if verbose:
                        print("Deleting file " + lbh + "/store/" + i + "/file.tar.gz")
                    os.remove(lbh + "/store/" + i + "/file.tar.gz")
                    os.remove(lbh + "/store/" + i + "/reference_tar")
                if not os.path.exists(lbh + "/store/" + i + "/file"):
                    shutil.rmtree(lbh + "/store/" + i)

def compress(filename, outputfile):
    with tarfile.open(outputfile, "w:gz") as tar:
        tar.add(filename)


verbose = False


def main():
    global verbose
    # ArgParse
    parser = argparse.ArgumentParser(description = '''Backr2 backup script''', epilog = '''Copyright (c) 2021 Anthony Fadly (18fadly.anthony@gmail.com)''')

    parser.add_argument('-l', '--location', metavar = '<path>', nargs = 1, type = str, default = [None], help = 'Location to store backup, will be ignored if .backr-location exists, defaults to ~/backr2')
    parser.add_argument('-s', '--source', metavar = '<path>', nargs = 1, type = str, default = [cwd], help = 'Source to backup, defaults to current directory')
    parser.add_argument('-r', '--restore', metavar = ('<path>', '<backup number>'), nargs = 2, type = str, default = '', help = 'restore from backup <backup number> to <path>')
    parser.add_argument('-gc', '--garbage-collect', action='store_true', help='Delete old backups')
    parser.add_argument('-d', '--default', action='store_true', help='Use default backup location: ' + default_location)
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Be verbose')
    parser.add_argument('-c', '--compress', action='store_true', default=False, help='Compress backups')
    parser.add_argument('-sc', '--smart-compress', action='store_true', default=False, help='Compress files only if they would compress to 90 percent or less of their original size')
    #parser.add_argument('-dc', '--decompress', action='store_true', default=False, help='Decompress backups during restore')

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
    table: FileTable = FileTable(file_list)

    if not os.path.exists(location + "/" + basehash):
        backup_number = 1
        mkdirexists(lbh)
        mkdirexists(lbh + "/store")
        mkdirexists(lbh + "/backups")
    else:
        backup_number = int(file_read(lbh + "/latest")) + 1

    mkdirexists(lbh + "/backups/" + str(backup_number))
    create_dirs(dir_list, basename, lbh + "/backups/" + str(backup_number))
    resolve_table(table, lbh, lbh + "/backups/" + str(backup_number), basename, backup_number, args.compress, args.smart_compress)
    file_overwrite(lbh + "/latest", str(backup_number))
    print("Completed backup to " + lbh + "/backups/" + str(backup_number))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('\n' + "exit")
        sys.exit(0)
