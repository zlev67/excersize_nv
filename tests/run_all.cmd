@echo off
echo Starting Telemetry Monitoring System...
echo.

echo [1/4] Starting Ingest Server on port 9002...
start "Ingest Server" cmd /k python ..\ingest_server\ingest_server.py

timeout /t 3 /nobreak >nul

echo [2/4] Starting API Server on ports 8080 and 9001...
start "API Server" cmd /k python ..\api_server\api_server.py

timeout /t 3 /nobreak >nul

echo [3/4] Starting Data Generator...
start "Data Generator" cmd /k python ..\data_generator\data_generator.py

timeout /t 3 /nobreak >nul

echo [4/4] Starting Data Reader...
start "Data Reader" cmd /k python data_reader_test.py

echo.
echo All components started!
echo Close any window to stop that component.
echo Press Ctrl+C in Ingest Server window to clean up database.
pause