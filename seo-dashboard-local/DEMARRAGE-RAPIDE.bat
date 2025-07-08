@echo off
echo 🎯 ================================
echo    Dashboard SEO Analytics
echo    Demarrage Automatique Windows
echo 🎯 ================================
echo.

echo 🔍 Verification Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js non trouve !
    echo 📥 Telecharge depuis: https://nodejs.org/
    echo 🔄 Redemarrer ce script apres installation
    pause
    exit
)

echo ✅ Node.js OK
echo.

echo 📦 Installation des dependances...
npm install express cors

echo.
echo 🚀 Demarrage du dashboard...
echo 🌐 Interface disponible sur: http://localhost:3000
echo.
echo ⏹️  Pour arreter: Ctrl + C
echo.

npm start

pause