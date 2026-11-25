@echo off
echo =========================================================
echo  Launching Automation Chrome on Port 9222
echo =========================================================
echo.
echo 1. Stopping conflicting background Chrome processes...
taskkill /F /IM chrome.exe >nul 2>&1
ping 127.0.0.1 -n 3 >nul

echo 2. Launching Chrome with port 9222...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir="c:\Users\mehak\Desktop\sheru automation\chrome_profile" "https://chatgpt.com" "https://flow.google.com"

ping 127.0.0.1 -n 3 >nul
echo.
echo Chrome is open and ready on port 9222!
