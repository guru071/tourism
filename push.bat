@echo off
git init
git add -A
git commit -m "Initial: AI Tourism Ecosystem complete"
git branch -M main
git remote remove origin 2>nul
git remote add origin https://github.com/guru071/tourism.git
git push -u origin main --force
