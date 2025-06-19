#!/bin/bash
set -e

# 1. Ο φάκελος εργασίας
WORKDIR="lambda_build"

# 2. Καθάρισε προηγούμενα builds
rm -rf $WORKDIR function.zip
mkdir -p $WORKDIR/python

# 3. Εγκατάσταση dependencies σε υποφάκελο 'python'
pip install --target "$WORKDIR/python" requests geopy boto3 feedparser

# 4. Αντιγραφή handler script (π.χ. handler.py)
cp handler.py $WORKDIR/

# 5. Δημιουργία zip (προσοχή: zip από μέσα στον φάκελο για σωστή δομή)
cd $WORKDIR
zip -r9 ../function.zip ./*
cd ..

echo "✅ Το function.zip δημιουργήθηκε επιτυχώς!"
