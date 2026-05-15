@echo off
set DIGEST_MODE=daily
cd /d "C:\Users\micae\reddit_digest"
C:\Python314\python.exe main.py >> "C:\Users\micae\reddit_digest\digest.log" 2>&1
