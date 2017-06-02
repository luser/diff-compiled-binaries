#!/usr/bin/env python

from __future__ import print_function
import operator
import os
import re
import string
import subprocess
import sys

jmp_or_call = re.compile(r'((jmp|je|jne|jae|ja|jb|call)\s+)[0-9A-F]+')
instructions = re.compile(r'^( [0-9A-F]{2})+')
def get_image_base(binary):
    p = subprocess.Popen(['dumpbin', '/headers', binary], stdout=subprocess.PIPE, stderr=open(os.devnull, 'w'))
    lines = [line for line in p.stdout if 'image base' in line]
    if p.wait() != 0 or len(lines) != 1:
        raise subprocess.CalledProcessError('dumpbin /headers failed')
    return int(lines[0].split('image base',1)[0].strip(), 16)

def disassemble_functions(binary, funcs):
    base = get_image_base(binary)
    for offset, length, name in funcs:
        print('%s:' % name)
        output = subprocess.check_output(['dumpbin', '/disasm',
                                          '/range:%d,%d' % (base + offset, base + offset + length),
                                          binary],
                                         stderr=open(os.devnull, 'w'))
        # Skip some header and footer gunk
        for line in output.splitlines()[7:-4]:
            if ':' not in line:
                continue
            # Strip offsets
            addr, rest = line.split(':', 1)
            # Strip jmp/call addrs
            m = jmp_or_call.search(rest)
            if m:
                rest = jmp_or_call.sub(r'\1...', rest)
                # Also strip the instruction bytes in this case
                m2 = instructions.match(rest)
                rest = instructions.sub(' xx' * (len(m2.group(0)) / 3), rest)
            print(rest)
        sys.stdout.write('\n\n')

def find_functions_in_file(sym_file, source_filename):
    source_id = None
    source_filename = source_filename.lower()
    in_func = None
    for line in open(sym_file, 'r'):
        line = line.rstrip()
        if source_id is None and line.startswith('FILE'):
            id, filename = line.split(None, 2)[1:]
            if filename.startswith('hg:'):
                filename = filename.split(':')[2]
            if os.path.basename(filename).lower() == source_filename:
                source_id = id
        if source_id is not None:
            if line.startswith('FUNC'):
                offset, size, _, name = line.split(None, 4)[1:]
                in_func = (int(offset, 16), int(size, 16), name)
            elif in_func is not None and all(x in string.hexdigits for x in line.split(None)[0]):
                line_source_id = line.split(None)[-1]
                if line_source_id == source_id:
                    yield in_func
                    in_func = None

def main():
    if len(sys.argv) != 4:
        print('disassemblestuff.py <path to binary> <path to symbol file> <source file name>')
        sys.exit(1)
    disassemble_functions(sys.argv[1], sorted(find_functions_in_file(sys.argv[2], sys.argv[3]), key=operator.itemgetter(2)))

if __name__ == '__main__':
    main()
