# mkdir bb tc
# mount buildbot dmg
# rsync -a /Volumes/Nightly/Nightly.app bb
# mount taskcluster dmg
# rsync -a /Volumes/Nightly/Nightly.app tc
# disassemble all Mach-O binaries in each bundle
for t in bb tc; do for f in $(find $t/Nightly.app/Contents/MacOS -type f -print0 | xargs -0  file -h | grep Mach-O | cut -f1 -d:); do echo $f; otool -tvV $f | tail -n +2 | sed -E -e 's/^[[:xdigit:]]{16}/0000000000000000/' > $t-$(basename $f).dis; done; done
# pip install unidiff
