# STEP 6: Try to apply every patch
rm -f applied/*
(cd issues && for p in *; do
    (cd ../applied && mkdir $p)
done)

PATCHES=$(cd patches && ls */*)
for p in $PATCHES; do
    (cd repo && git reset --hard && git apply ../patches/$p && git diff > ../applied/$p)
done
