#!/bin/bash
(cd applied && ls -1 */* | xargs python ../../git-patchops.py | sort | python ../../git-checkops.py > ../potential-conflicts.txt)
python ../git-eliminate-common-dirname.py potential-conflicts.txt > detected-conflicts.txt
python dot-conflicts.py detected-conflicts.txt > detected-conflicts.dot
dot -Tsvg detected-conflicts.dot > detected-conflicts.svg
