Git Patchpatrol
===============

In issue trackers of big open source projects the number of proposed changes
and bug fixes may grow big. When that happens it becomes difficult not only for
maintainers to stay on top of the patch queue but also for contributors to
avoid working on solutions interfering with other proposed changes or even
duplicating work.

Given a set of patches and a git repository, patchpatrol determines for every
patch the files and lines it affects. With this information a report of
overlapping patches is generated.

Git patchpatrol is like running git-blame on the future.


Usage:
------

patchpatrol update <database> repo-url patch-directory
    [commit, commit, commit | commit..commit | branch]
    -t tmp-directory (hint: /dev/shm)

patch-directory/
    <issue-1>/
        patch-1.diff
    <issue-2>/
        patch-2.diff
        patch-3.diff
    <some>/
        <arbitrary>/
            <reference/>
                patch-x.diff


Filesystem-Database structure (.gitpp):
---------------------------------------
changesets.txt  // <- Index of tested changesets
patches.txt     // <- Index of tested patches

patches/
    <ef>/<sha1-blob-patch>
        *.ref           // <- File name, reference (issue-nr...), url
                        //    Probably we want to move this into a global index
        *.cnf           // <- Target branches (min-changeset, max-changeset)
                        //    Probably we want to move this into a global config
        *.diff          // <- Original patch

blobs/
    <xy>/<sha1-blob-1>/
        patch-sha1-1.hunks
    <xy>/<sha1-blob-2>/
        patch-sha1-1.hunks
        patch-sha1-2.hunks
    <xz>/<sha1-blob-3>/


Queries:
* SHOULD TEST? (changeset, patch)
  -> yes, no
* STATUS? (changeset, patch)
  -> success, fail
* AFFECTED LINES? (changeset [, patch]) -> list blobs via git-ls-tree
* AFFECTED LINES? (blob [, patch])

Analyzis:
* OVERLAPS? ([changeset [, patch]])
    -> <blob> line bc <patch>
    -> <blob> line bp <patch>
    -> <blob> line ep <patch>
    -> <blob> line ec <patch>

Execution plan:
    # Generate tmp directory
    # Clone git repository into generated tmp/repo directory (clone --mirror)
    # Enumerate commits in source
    # Enumerate patches in source
    # For each commit in source:
    ##  git checkout commit (detached-head)
    ##  For each patch in source:
    ###   Determine whether patch should be tested in that commit
    ####    Does a result already exist? continue.
    ####    Custom filter?
    ###   git-clone tmp/repo -> tmp/working (using hardlinks)
    ###   if git-apply patch --log <commit>/logs/<patch>.log:
    ####    git-diff > <commit>/applied/<patch>.diff
    ####    parse hunks

Parse hunks:
    # For each index-line:
    ##  Ensure blob exists
    ##  Ensure blob is linked to commit
    # For each hunk-line:
    ##  Ensure dirname of patch exists
    ##  Write hunk events
