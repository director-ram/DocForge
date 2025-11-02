@echo off
REM Batch script to complete all AI answer generation
REM This will run until all 668 questions are answered

echo ========================================
echo   AI Answer Generation - Full Run
echo ========================================
echo.
echo This will generate AI answers for all 668 questions
echo Progress is saved every 20 questions
echo You can stop anytime with Ctrl+C and resume later
echo.
echo Starting in 3 seconds...
timeout /t 3 /nobreak >nul

cd /d "c:\Users\khema\Desktop\DOC_forge\Hemasai-work\director-ram-DocForge\docquest-extractor"

:loop
echo.
echo [%date% %time%] Checking progress...
C:\Users\khema\AppData\Local\Programs\Python\Python312\python.exe scripts\check_progress.py

echo.
echo [%date% %time%] Running AI answer generation...
C:\Users\khema\AppData\Local\Programs\Python\Python312\python.exe scripts\auto_answer_with_ollama.py --model gemma2:9b --batch-size 20 --max 100

REM Check if we should continue
C:\Users\khema\AppData\Local\Programs\Python\Python312\python.exe -c "import json; answers = json.load(open('data/ai_generated_answers.json')); exit(0 if len(answers) >= 668 else 1)"

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   ALL QUESTIONS ANSWERED!
    echo ========================================
    echo.
    echo Generating final PDF with all answers...
    C:\Users\khema\AppData\Local\Programs\Python\Python312\python.exe scripts\generate_answered_pdf.py "Living Word.pdf" "Living Word_Complete_AI.pdf" --answers data\ai_generated_answers.json
    echo.
    echo Done! Check: Living Word_Complete_AI.pdf
    pause
    exit /b 0
) else (
    echo.
    echo Continuing with next batch...
    timeout /t 2 /nobreak >nul
    goto loop
)
