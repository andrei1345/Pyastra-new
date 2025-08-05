#!/usr/bin/python
############################################################################
# $Id: pyastra 105 2004-12-24 20:38:25Z estyler $
#
# Description: Console front-end. Pyastra project.
# Author: Alex Ziranov <estyler _at_ users _dot_ sourceforge _dot_ net>
#    
# Copyright (c) 2004 Alex Ziranov.  All rights reserved.
#
############################################################################
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
############################################################################

#Exit codes:
# 0 - ok
# 1 - unsupported feature request
# 2 - syntax error
# 3 - hardware limitations error
# 4 - arguments error
#
#Built-in functions:
# asm - include verbatim asm text
# halt - halt the system
#

import sys, os, os.path, compiler, getopt, pyastra.ports.pic14.procs
from pyastra.ports.pic14.tree2asm import tree2asm
from pyastra.tree2tree import tree2tree
import ast
#from getopt import getopt

NFO='pyastra 0.0.4.1'
ports=('pic14',)
ICD = 0
ASSEMBLERS=(('gpasm', ''), ('mpasm.exe', ''), ('mpasmwin.exe', ''),)
#
# By default optimizes for size,
# but if op_speed=1 than optimizes for speed.
# 
op_speed = 0
compile_only = 0

errors=0
warnings=0
messages=0


def usage():
    print("""%s usage:
pyastra [options] infile

Options:
  -m              Set the port to use (default: -m%s)
  -mlist          List available ports
  -p              Select port specific processor (default: -m%s -p%s)
  -plist          List supported port specific processors
      --icd       Enable ICD support (disabled by default)
      --op-speed  Optimize for speed (for code size by default)
  -S  --compile   Compile only, don't assemble or link.    
  -o  --output    Alternate name of output file.
  -h, --help      Show this usage message and exit
""" % (NFO, ports[0], ports[0], next(procs_clean), ))
    sys.exit(4)

def say(message, line=None, level=tree2asm.error, exit_status=0):
    global errors, warnings, messages
    
    if line is not None:
        print('%s: %g: %s' % (level, line, message))
    else:
        print('%s: %s' % (level, message))

    if exit_status:
        sys.exit(exit_status)
        
    if level==tree2asm.error:
        errors += 1
    elif level==tree2asm.warning:
        warnings += 1
    else:
        messages += 1
            

print("""
WARNING: This is a preview release! It may (but i hope it doesn\'t) generate incorrect code.

If it really works, please inform me for which microcontroller did you used Pyastra and other thigs that may be important:
estyler (at) users (dot) sourceforge (dot) net

If you have found a bug, you are welcome to submit one:
http://sourceforge.net/tracker/?group_id=106265&atid=643744

-------
""")

procs=pyastra.ports.pic14.procs.__all__
procs_clean = filter(lambda item: item[-1]!='i', procs)
PROC=next(procs_clean)
out_name=None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'o:hm:p:S', ['output=', 'help', 'icd', 'op-speed', 'compile',])
except getopt.GetoptError:
    usage()

for o, a in opts:
    if o in ('-h', '--help'):
        usage()
        sys.exit()
    if o=='--op-speed':
        op_speed = 1
    elif o in ('-S', '--compile'):
        compile_only=1
    elif o in ('-o', '--output'):
        out_name=os.path.splitext(a)[0]
    elif o=='--icd':
        ICD = 1
    elif o=='-m':
        if a=='list':
            print('Available ports: %s' % str(ports))
            sys.exit(0)
        elif a!='pic14':
            print("""Curent version supports pic14 (Microchip PIC16*) only.
Please submit feature request if that port is not already in TODO:
http://sourceforge.net/tracker/?atid=643747&group_id=106265&func=browse""")
            sys.exit(4)
    elif o=='-p':
        if a=='list':
            print('%i supported %s-port specific processors:\n%s' % (len(procs_clean), ports[0], str(procs_clean)))
            sys.exit(0)
        elif a in procs_clean:
            PROC=a
        else:
            print("""%s processor is not supported by the current version.
(Have you selected a correct port?)
Please submit feature request if that processor is not already in TODO:
http://sourceforge.net/tracker/?atid=643747&group_id=106265&func=browse""" % 
            sys.exit(4))

if not args:
    usage()

root=ast.parse(args[0])

if not out_name:
    out_name=os.path.splitext(args[0])[0]

if ICD:
    if PROC + 'i' not in procs:
        print('Seems like microcontroller %s doesn\'t support ICD.' % PROC)
        sys.exit(4)
    else:
        print("Compiling from %s to %s for processor %s (port %s)..." % (
              args[0], out_name+'.asm', PROC, 'pic14'))
        PROC += 'i'

op=tree2tree(root, say)
p=tree2asm(ICD, op_speed, PROC, say)
p.convert(op.root)

pstr = 'Compiler has found'
ptest = 0
if errors:
    pstr += ' %g errors' % errors
if warnings:
    if ptest:
        pstr +=','
    pstr += '%g warnings' % warnings
if messages:
    if ptest:
        pstr +=','
    pstr += '%g messages' % messages

if ptest:
    print(pstr+'.')

if errors:
    print('No asm code generated.')
    sys.exit(1)

out=open(out_name+'.asm', 'w')

out.write(""";
; Generated by %s
; infile: %s
;
""" % (NFO, args[0],))

out.write(p.get_asm())

out.close()

print("Peak RAM usage: %g byte(s) (%.1f%%)" % (p.ram_usage, p.ram_usage*100./p.max_ram))
print("Program memory usage: %g word(s) (%.1f%%)" % (p.instr, p.instr*100./p.max_instr))
if p.asm:
    print("NOTE: statistics includes verbatim data specified in asm function!")
if ICD:
    print("NOTE: statistics includes ICD memory usage!")

print

if not compile_only and hasattr(os, 'access'):
    asm=asm_path=asm_args=None

    if os.environ.has_key('PATH'):
        paths=os.environ['PATH']
    else:
        paths=defpath
        
    for path in paths.split(os.pathsep):
        for fn, args in ASSEMBLERS:
            if os.access(os.path.join(path, fn), os.X_OK):
                asm_path = os.path.join(path, fn)
                asm = fn
                asm_args = args
                break

        if asm_path:
            break

    if asm_path:
        print('Assembling %s with %s...' % (out_name+'.asm', asm,))
        print('"%s" %s %s' % (asm_path, out_name+'.asm', asm_args))
        os.system('"%s" %s %s' % (asm_path, out_name+'.asm', asm_args))
    else:
        print('No assembler found. Supported assemblers are: %s' % (ASSEMBLERS, ))

    print()
