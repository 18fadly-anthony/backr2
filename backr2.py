#!/usr/bin/env python3

# Copyright (c) 2020 Anthony Fadly (18fadly.anthony@gmail.com)
# This program is licensed under the Apache License 2.0
# You are free to copy, modify, and redistribute the code.
# See LICENSE file.

# Backr 2: Complete rewrite of backr-py

# Imports
import os
import argparse

home = os.path.expanduser('~')
default_location = home + "/backrs"
cwd = os.getcwd()

# Define general functions
def mkdirexists(dir):
    if not(os.path.isdir(dir)):
        os.mkdir(dir)


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


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('\n' + "exit")
        sys.exit(0)
