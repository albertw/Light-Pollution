#!/usr/bin/env python
import argparse

import observations

parser = argparse.ArgumentParser(description='SQM datafile processing.')

parser.add_argument('-i', required=True, help="Input logfile", dest='infile')

command_group = parser.add_mutually_exclusive_group(required=True)
command_group.add_argument('-d', dest='dark', action='store_true',
                           help='output only the rows where the Sun is below minsun '
                                'and the Moon below minmoon')
command_group.add_argument('-t', dest='antitransit', action='store_true',
                           help='output only the rows an hour either side of the solar '
                                'midnight (the  solar antitransit time for that night)')

parser.add_argument('-m', '--minmoon', dest='minmoon', type=float, default='-10',
                    help='Minimum altitude of the Moon in degress relaive to the horizon '
                         'to consider for --dark. (Default: %(default)s)')
parser.add_argument('-s', '--minsun', dest='minsun', type=float, default='-18',
                    help='Minimum altitude of the Sun in degress relaive to the horizon '
                         'to consider for --dark. (Default: %(default)s)')
parser.add_argument('-o', '--outfile', dest='outfile', default='stdout',
                    help='File to write output to. (Default: %(default)s).')
args = parser.parse_args()

SQM = observations.Datafile()
SQM.read(args.infile)
SQM.compute()

SQM.reduce_dark(sunlow=args.minsun, moonlow=args.minmoon)

if args.antitransit:
    SQM.reduce_midnight()

if args.outfile == "stdout":
    SQM.write()
else:
    SQM.write(args.outfile)
