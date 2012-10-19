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

When deploying patchpatrol for your git repository, it will answer the
following questions:

A:  Givan a repo, a set of patches and a single commit:
    1.  For all patches which apply properly the object-ids and line numbers
        where they apply in the specified commit.
    2.  List of patches which do not apply.

B:  Given a repo, a single patch and a range of commits:
    1.  Subranges of commits where the patch applies successfully / fails.

Requirements:
------------

Needs git python with patch applied:
https://github.com/gitpython-developers/GitPython/pull/77

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

Filesystem-Structure (detached head):
-------------------------------------

changesets.txt          // <- Index of tested changesets
patches.txt             // <- Index of tested patches
rules.txt               // <- Testing rules (restrict patch to branch commit..range)

patches/
    some/scheme/patch.diff
    other/patch-2.diff


Schedule:

Determine which changesets must be tested for which patches
for each patch do:
    1. Extract paths of affected files
    2. Determine changesets for affected files using git rev-list
    3. Update map: changeset -> [patches]

Schedule Filter:
* FILTER (patch)
  -> Not before date|commit
    -> Could be populated automatically by patch file ctime 
  -> Not after date|commit
    -> Could be populated automatically when patch was commited


* Starthint: commit-id -- default: mtime
* -> Last sucessfull application
* -> First failing application

Result cache:
-------------
* EXISTS? (patch, blob)
  -> yes/no
* GET (patch, blob)
  -> hunk-events|empty list
* PUT (patch, blob, hunk-events)

blob resolver:
* Given a patch and a changeset/list of changesets/range, return the commits,
  affecting one or more files mentioned in the patch.
  -> git rev-list <commit> -- <paths>

* RESOLVE (changeset, patch)
  -> map(pathname -> {changeset => blob, ...})

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
