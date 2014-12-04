#!/usr/bin/env python

from datetime import datetime, date, timedelta
import re
import os
import sys
import argparse
import glob
import shutil
import filecmp
# import hexdump

# Written by Chad Sherrell.
# import g2_crc
from crctable import CalculateCRC32

timestamp = datetime.today()
yesterday = date.today() - timedelta(1)

parser = argparse.ArgumentParser(description='File Merger for GSQA logging')
parser.add_argument('-p', '--path',
                    action='store',
                    default="/home/cmorgan/file_merger/data/",
                    help="Directory that contains the two terminal server \
                    folders and the GOLD folder. \
                    Default: /home/cmorgan/file_merger/data")
parser.add_argument('-d', '--date',
                    action='store',
                    default=yesterday.strftime('%Y%m%d'),
                    help="Date you wish to compare. YYYYMMDD")
parser.add_argument('-l', '--log',
                    action='store',
                    default="/home/cmorgan/file_merger/log_file.txt",
                    help="File to be used for logging. \
                    Ex. /home/cmorgan/file_merger/log_file.txt")
parser.add_argument('-D', '--debug', action='store_true', default=False,
                    help="Add the -d if you prefer debug mode. \
                    Give me ALL the print statements!")
args = parser.parse_args()


def clean_exit():
    fd_log.write("File 1 is: %s bytes\n" % (bfile_1_size))
    fd_log.write("File 2 is: %s bytes\n" % (bfile_2_size))
    fd_log.write("Total bytes read: %s\n" % (total_read))
    fd_log.write("\nDone. Closing files.\n")
    fd_log.close()
    print "\n\n"
    print i, "  iterations"
    print total_read, "  Total Bytes Read"
    # If file 1 or 2 were not present,
    # then bfile_1 and bfile_2 never got defined.
    if file_1 == '' or file_2 == '':
        sys.exit()
    else:
        bfile_1.close()
        bfile_2.close()
        bfile_gold.close()
        sys.exit()

# Hex Dumper (from http://code.activestate.com/recipes/142812-hex-dumper)
FILTER = ''.join([(len(repr(chr(x))) == 3) and chr(x) or '.'
                  for x in range(256)])


def dump2hex(src, length=8):
    result = []
    for i in xrange(0, len(src), length):
        s = src[i:i+length]
        hexa = ' '.join(["%02X" % ord(x) for x in s])
        printable = s.translate(FILTER)
        result.append("%04X   %-*s   %s\n" % (i, length*3, hexa, printable))
    return ''.join(result)

# For debugging
i = 0
x = 0
total_read = 0

# Create tables for CRC and timestamp reference.
file1_table = open('/home/cmorgan/file_merger/table1', 'a')
file2_table = open('/home/cmorgan/file_merger/table2', 'a')

# Open log file for appending.
fd_log = open(args.log, 'a')

# If the debug option is active, print to screen rather than the log file.
if args.debug is True:
    print "%s" % (timestamp)
    print "Parsing GSQA collection files for: %s\n" % (args.date)
else:
    fd_log.write("\n\n****************** %s *****************\n" % (timestamp))
    fd_log.write("Parsing GSQA collection files for: %s\n\n" % (args.date))

os.chdir(args.path)
file_1 = ''
file_2 = ''

# Search data directory for all files from a specified date.
file_1 = ''.join(glob.glob("termserv2/%s*.log" % (args.date)))
if args.debug is True:
    print "File from terminal server 1: ", file_1
file_2 = ''.join(glob.glob("termserv3/%s*.log" % (args.date)))
if args.debug is True:
    print "File from terminal server 2: ", file_2

# Early check to see if one of the files is missing.
# If file 1 is missing, copy file 2 and zip.
if file_1 == '' and file_2 != '':
    if args.debug is True:
        print "File 1 missing. Using File 2."
    else:
        fd_log.write("WARNING: File 1 missing. Using File 2.\n")
    gold_file = file_2.split('/')
    gold_file = gold_file[1]
    gold_file = 'gold_files/' + gold_file
    shutil.move(args.path + file_2, args.path + gold_file)
    os.system('gzip %s' % (gold_file))
    clean_exit()

# If file 2 is missing, copy file 1 and zip.
elif file_2 == '' and file_1 != '':
    if args.debug is True:
        print "File 2 missing. Using File 1."
    else:
        fd_log.write("WARNING: File 2 missing. Using File 1.\n")
    gold_file = file_1.split('/')
    gold_file = gold_file[1]
    gold_file = 'gold_files/' + gold_file
    shutil.move(args.path + file_1, args.path + gold_file)
    os.system('gzip %s' % (gold_file))
    clean_exit()

# Both files are missing. Something is jacked.
elif file_1 == '' and file_2 == '':
    if args.debug is True:
        print "GSQA is broken..."
    else:
        fd_log.write("ERROR: Both files are missing for the date requested. \
                     Check terminal servers.")
    clean_exit()

# Creates gold_file with same name as collection file.
gold_file = file_1.split('/')
gold_file = gold_file[1]
gold_file = 'gold_files/' + gold_file

# Compare both files. Filecmp runs the os.stat() command.
# The files are identical
if filecmp.cmp(file_1, file_2) is True:
    if args.debug is True:
        print "FILES ARE THE SAME. Deleting: ", args.path + file_2
        print "Moving ", args.path + file_1, " to: ", args.path + gold_file
    else:
        fd_log.write("Files are the same. Deleting duplicate and moving \
                     one copy.\n")
    # Remove duplicate file.
    os.remove(args.path + file_2)
    # Move file 1 to gold folder.
    shutil.move(args.path + file_1, args.path + gold_file)
    os.system('gzip %s' % (gold_file))  # Zip new gold file.

# The files are not identical. Time for a line-by-line comparison.
else:
    fd_log.write("Files are not the same. Beginning line-by-line comparison\n")
    bfile_1 = open(file_1, 'rb')
    bfile_2 = open(file_2, 'rb')

    bfile_1_size = os.path.getsize(file_1)
    bfile_2_size = os.path.getsize(file_2)

    # Determine the largest file size so
    # merger knows when to quit reading in bytes.
    if bfile_1_size >= bfile_2_size:
        max_file_size = bfile_1_size
    else:
        max_file_size = bfile_2_size

    # Buffer size was determined by the
    # largest possible receiver log x 2 (double).
    buffsize = 16384
    bfile_gold = open('%s%s' % (args.path, gold_file), 'ab')

    start_1 = 0
    start_2 = 0

    buffer_1 = ''
    buffer_2 = ''

    # All G2 receiver logs start with 'AA 44 12'
    header = re.compile(chr(0xAA) + chr(0x44) + chr(0x12))

    while total_read <= max_file_size:
        buffer_in_1 = bfile_1.read(buffsize)
        buffer_in_2 = bfile_2.read(buffsize)

        # for the first run, buffer_1[start_1:] is ''.
        # Every run after that it appends new read buffer_in
        # to previous buffer.
        buffer_1 = bytearray(buffer_1[start_1:] + buffer_in_1)
        buffer_2 = bytearray(buffer_2[start_2:] + buffer_in_2)

        if args.debug is True:
            print "Length of new buffer_1: ", len(buffer_1)
            print "Length of new buffer_2: ", len(buffer_2)
        else:
            fd_log.write("Length of new buffer_1: %s\n" % len(buffer_1))
            fd_log.write("Length of new buffer_2: %s\n\n" % len(buffer_2))

        while buffer_in_1 != '':
            # On the first iteration this does nothing.
            # From second iteration on, this sets buffer_* to start at last
            # found log header because start_* is reassigned at the end of
            # the while loop.
            buffer_1 = buffer_1[start_1:]
            buffer_2 = buffer_2[start_2:]

            match_1 = header.search(buffer_1, start_1)
            match_2 = header.search(buffer_2, start_2)

            # Searches the buffers for header bytes and returns position of
            # first found header. end_log_* is the location of the next found
            # header in binary file. if next head cannot be found, break out
            # and read in more of the file.
            try:
                if args.debug is True:
                    print "Start of header found at location: ", \
                          int(match_1.start())
                else:
                    fd_log.write("Start of header found at location: %s\n"
                                 % (int(match_1.start())))
                end_log_1 = header.search(buffer_1[int(match_1.start())+4:
                                                   buffsize])
                next_header_loc = int(end_log_1.start() + match_1.start())
                if args.debug is True:
                    try:
                        print "Next header found at location: ", \
                              next_header_loc
                    except AttributeError:
                        break
                else:
                    fd_log.write("Next header found at location: %s\n"
                                 % (next_header_loc))
                end_log_2 = header.search(buffer_2[int(match_2.start())+4:
                                                   buffsize])
            except AttributeError:
                end_log_1 = False
                end_log_2 = False
                break

            # On the first iteration we must figure out which file has more
            # data before the start of the first complete log.
            if i == 0:
                if match_1.start() > match_2.start():
                    bfile_gold.write(buffer_in_1[start_1:match_1.start()])
                    bfile_gold.flush()
                elif match_2.start() > match_1.start():
                    bfile_gold.write(buffer_in_2[start_2:match_2.start()])
                    bfile_gold.flush()
                else:
                    bfile_gold.write(buffer_in_1[start_1:match_1.start()])
                    bfile_gold.flush()

            # match.start() gives the byte
            # position of the first found header.
            # current_log_* is the log under review in each file.
            try:
                current_log_1 = buffer_1[
                    int(match_1.start()):(int(match_1.start() +
                                              end_log_1.start()))]
            except AttributeError:
                if args.debug is True:
                    print "end of log not found"
                break
            try:
                current_log_2 = buffer_2[
                    int(match_2.start()):(int(match_2.start() +
                                              end_log_2.start()))]
            except AttributeError:
                if args.debug is True:
                    print "end of log not found"
                break

            # CRC that is given from the receiver.
            g_crc_1 = False
            try:
                g_crc_1 = ((buffer_1[end_log_1.start() +
                                     match_1.start() + 3] << 24) +
                           (buffer_1[end_log_1.start() +
                                     match_1.start() + 2] << 16) +
                           (buffer_1[end_log_1.start() +
                                     match_1.start() + 1] << 8) +
                           (buffer_1[end_log_1.start() + match_1.start()]))
            except AttributeError:
                print "Could not find given CRC for file 1"
                print "Total bytes read: ", total_read
                break

            g_crc_2 = False
            try:
                g_crc_2 = ((buffer_2[end_log_2.start() +
                                     match_2.start() + 3] << 24) +
                           (buffer_2[end_log_2.start() +
                                     match_2.start() + 2] << 16) +
                           (buffer_2[end_log_2.start() +
                                     match_2.start() + 1] << 8) +
                           (buffer_2[end_log_2.start() + match_2.start()]))
            except AttributeError:
                print "Could not find given CRC for file 2"
                print "Total bytes read: ", total_read
                break

            # Calculate the CRC using Chad's module "g2_crc" and CRC table.
            c_crc_1 = int(CalculateCRC32(len(current_log_1), current_log_1))
            c_crc_2 = int(CalculateCRC32(len(current_log_2), current_log_2))

            if args.debug is True:
                print "The given CRC for current log 1: ", g_crc_1
                print "The calculated CRC for current log 1: ", c_crc_1
                print "The given CRC for current log 2: ", g_crc_2
                print "The calculated CRC for current log 2: ", c_crc_2

            else:
                fd_log.write("The given CRC for current log 1: %s\n"
                             % (g_crc_1))
                fd_log.write("The calculated CRC for current log 1: %s\n"
                             % (c_crc_1))
                fd_log.write("The given CRC for current log 2: %s\n"
                             % (g_crc_2))
                fd_log.write("The calculated CRC for current log 2: %s\n"
                             % (c_crc_2))

            # If the given CRC matches the calculated CRC , write the log to
            # the gold file.
            if g_crc_1 == c_crc_1 and g_crc_1:
                # The given and calculated from file 1 match and are not blank.
                # The given and calculated for file 2 match.
                log_details_1 = []
                log_details_1.append(g_crc_1)
                log_details_1.append(int(match_1.start()))
                log_details_1.append(int(match_1.start())
                                     + int(end_log_1.start()))
                log_details_1.append('XX:XX:XX')
                if g_crc_2 == c_crc_2 and g_crc_1 == g_crc_2:
                    log_details_2 = []
                    log_details_2.append(g_crc_2)
                    log_details_2.append(int(match_2.start()))
                    log_details_2.append(int(match_2.start())
                                         + int(end_log_2.start()))
                    log_details_2.append('XX:XX:XX')
                    # Write file 1 log to gold file.
                    bfile_gold.write(current_log_1)
                    bfile_gold.flush()
                    if args.debug is True:
                        print "GOOD. Given: ", g_crc_1, \
                              "Calc: ", c_crc_1, "\n\n"
                    else:
                        fd_log.write("GOOD. Given: %s" % (g_crc_1))
                        fd_log.write("Calc: %s\n\n" % (c_crc_1))

                if g_crc_2 == c_crc_2 and g_crc_1 != g_crc_2:
                    print "\n\nLogs are out of alignment!!!"
                    print "Given_1: ", g_crc_1, \
                          "Calc_1: ", c_crc_1, "\n\n"
                    print "Given_2: ", g_crc_2, \
                          "Calc_2: ", c_crc_2, "\n\n"
                    # For debugging
                    x = x + 1
                    if x == 10:
                        clean_exit()

                # The given and calculated for file 2 DO NOT match.
                if g_crc_2 != c_crc_2:
                    # Write file 1 log to gold file.
                    bfile_gold.write(current_log_1)
                    bfile_gold.flush()
                    if args.debug is True:
                        print "GOOD. file 1 crc is good. file 2 is not\n\n"
                    else:
                        fd_log.write("GOOD. file 1 crc is good. \
                                     file 2 is not\n\n")

            elif g_crc_1 is False:  # Given CRC for file 1 is blank!
                if args.debug is True:
                    print "Not Good. given crc is blank\n\n"
                else:
                    fd_log.write("Not Good. given crc is blank\n\n")

            # The given CRC did not match the calculated for file 1,
            # or was blank.
            else:

                # Given CRC matches calculated for file 2.
                if g_crc_2 == c_crc_2:
                    # Write log from file 2 to gold file.
                    bfile_gold.write(current_log_2)
                    bfile_gold.flush()
                    if args.debug is True:
                        print "GOOD. file 2 crc is good. file 1 is not\n\n"
                    else:
                        fd_log.write("GOOD. file 2 crc is good. \
                                     file 1 is not\n\n")

                # Given and Calculated CRCs for file 2 do not match.
                elif g_crc_2 != c_crc_2:
                    # The givens match and the calculated match, both servers
                    # saw same gap in data.
                    if g_crc_1 == g_crc_2 and c_crc_1 == c_crc_2:
                        if args.debug is True:
                            print "WARNING: Both terminal servers experienced \
                                    same gap in data. Writing from termserv1 \
                                    and continuing."
                        else:
                            fd_log.write("WARNING: Both terminal servers \
                                           experienced same gap in data. \
                                           Writing from termserv1 and \
                                           continuing.")
                        bfile_gold.write(current_log_1)
                        bfile_gold.flush()

                    else:
                        if args.debug is True:
                            print "Not Good.Given_1: ", g_crc_1,\
                                  "  Calc_1: ", c_crc_1, \
                                  "  Given_2: ", g_crc_2,\
                                  "  Calc_2: ", c_crc_2, \
                                  "  Iteration: ", i, \
                                  "  Total bytes read so far: ", total_read, \
                                  "\n\n"
                        else:
                            fd_log.write("ERROR: The Calculated and Given CRCs\
                                         did not match for either log.\n\
                                         ->Given_1: %s,  Calc_1: %s\n\
                                         ->Given_2: %s ,  Calc_2: %s\n\
                                         ->Iteration: %s ,  \
                                         Total bytes read so far: %s\n\n"
                                         % (g_crc_1, c_crc_1, g_crc_2,
                                            c_crc_2, i, total_read))
                        bfile_gold.write(current_log_1())
                        bfile_gold.flush()

            start_1 = int(end_log_1.start())
            start_2 = int(end_log_2.start())

            i = i + 1

            total_read = total_read + len(current_log_1)
            # for i in log_details_1:
            file1_table.write("%s" % log_details_1)
            file2_table.write("%s" % log_details_2)

        if buffer_in_1 == '':
            break

clean_exit()
