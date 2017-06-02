#!/usr/bin/env python

from difflib import SequenceMatcher
import glob
import os
import unidiff
import string
import subprocess
import sys

def diff(f1, f2):
    p = subprocess.Popen(['diff', '-u', f1, f2], stdout=subprocess.PIPE)
    stdout, _ = p.communicate()
    return unidiff.PatchSet(stdout.splitlines(True))

def non_hex_changes(a, b):
    matcher = SequenceMatcher(a=a, b=b)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            continue
        if tag != 'replace':
            print 'tag: ', tag
            return True
        a_ = a[i1:i2]
        b_ = b[j1:j2]
        if not (all(c in string.hexdigits for c in a_) and all(c in string.hexdigits for c in b_)):
            return True
    return False

def filter_hunks(d):
    for hunk in d:
        added = [l.value for l in hunk if l.is_added]
        removed = [l.value for l in hunk if l.is_removed]
        if len(added) != len(removed):
            yield hunk
        elif any(non_hex_changes(a, r) for a, r in zip(added, removed)):
            yield hunk

def main():
    patch = diff(sys.argv[1], sys.argv[2])
    if patch:
        d = patch[0]
        d[:] = list(filter_hunks(d))
        if d:
            print d

if __name__ == '__main__':
    main()
