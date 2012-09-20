# Settings
PAGES=48
PROJECT=drupal
FILTER="&status[]=13&status[]=8&status[]=14&version[]=8.x"

# STEP 1: Download listing pages of the specified tracker into the 'listings'
# subdirectory

# Cleanup old stuff
truncate -s0 listings-urls.txt
rm -f listings/*

for ((i=0;i<$PAGES+1;i++)); do
    echo "http://drupal.org/project/issues/search/$PROJECT?page=$i$FILTER" >> listings-urls.txt
done

(cd listings && wget -i ../listings-urls.txt)

# STEP 2: Extract issue urls from listing pages
sed -n 's#.*href="\(/node/[0-9]\{1,\}\).*#http://drupal.org\1#p' listings/* | \
    sort -n -k5 -t'/' -r > issues-urls.txt

# STEP 3: Download issue pages into the subdirectory 'issues'
(cd issues && wget -i ../issues-urls.txt)

# STEP 4: Extract patch urls from issue pages
rm -rf patches/*
(cd issues && for p in *; do
    mkdir ../patches/$p
    sed -n 's#.*pift-pass.*href="\(http://drupal\.org/files/[^"]\{1,\}\).*#\1#p' $p > ../patches/$p-urls.txt
done)

# STEP 5: Download all patches
rm -f patches/*/*
(cd issues && for p in *; do
    (cd ../patches/$p && wget -i ../$p-urls.txt)
done)

# STEP 6: Try to apply every patch
rm -f applied/*
(cd issues && for p in *; do
    (cd ../applied && mkdir $p)
done)

PATCHES=$(cd patches && ls */*)
for p in $PATCHES; do
    (cd repo && git reset --hard && git apply ../patches/$p && git diff > ../applied/$p)
done
