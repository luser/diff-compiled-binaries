#!/usr/bin/env python

from collections import defaultdict
from difflib import SequenceMatcher
import glob
import os
import unidiff
import string
import subprocess
import sys
from tempfile import NamedTemporaryFile

def diff(s1, s2):
    with NamedTemporaryFile() as f1, NamedTemporaryFile() as f2:
        f1.write(s1)
        f1.flush()
        f2.write(s2)
        f2.flush()
        p = subprocess.Popen(['diff', '-u', f1.name, f2.name], stdout=subprocess.PIPE)
        stdout, _ = p.communicate()
        return unidiff.PatchSet(stdout.splitlines(True))

def non_hex_changes(a, b):
    matcher = SequenceMatcher(a=a, b=b)
    it = iter(matcher.get_opcodes())
    for tag, i1, i2, j1, j2 in it:
        if tag == 'equal':
            continue
        a_ = a[i1:i2]
        b_ = b[j1:j2]
        if not (all(c in string.hexdigits for c in a_) and all(c in string.hexdigits for c in b_)):
            if '## symbol stub for:' in b_ or a_.startswith(' ## '):
                continue
            return True
    return False

def filter_hunks(d):
    for hunk in d:
        added = [l.value for l in hunk if l.is_added]
        removed = [l.value for l in hunk if l.is_removed]
        if len(added) != len(removed):
            yield hunk
        elif any(non_hex_changes(r, a) for a, r in zip(added, removed)):
            yield hunk

def split_functions(f):
    funcs = defaultdict(list)
    last = None
    for line in open(f, 'rb'):
        if line.endswith('section\n'):
            continue
        if line.endswith(':\n'):
            last = line[:-2]
        else:
            funcs[last].append(line)
    return funcs

def main():
    f1 = split_functions(sys.argv[1])
    f2 = split_functions(sys.argv[2])
    for f in f1.iterkeys():
        if f in f2:
            patch = diff(''.join(f1[f]), ''.join(f2[f]))
            if patch:
                d = patch[0]
                hunks = list(filter_hunks(d))
                if hunks:
                    print f, ': '
                    for h in hunks:
                        print h
    for f in set(f1.keys()) - set(f2.keys()):
        print f, ': '
        print ''.join('-' + l for l in f1[f])
    for f in set(f2.keys()) - set(f1.keys()):
        print f, ': '
        print ''.join('+' + l for l in f1[f])

if __name__ == '__main__':
    main()
