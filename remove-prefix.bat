@echo off
SetLocal EnableDelayedExpansion
set Pasta=%~dp0

:Inicio
CLS
ECHO.
Echo Informe a frase que deseja substituir
echo. 
set /p "Original=Original: "
echo.
Echo Informe a nova frase
echo.
set /p "Substituir=Substituir: "

for /f "Delims=" %%a in ('dir /b /a-d ^|find /v "%~nx0"') do (
set "Nome=%%a"
call :Renomear
)
echo.
pause
goto :Inicio

:Renomear
set "Nome2=!Nome:%Original%=%Substituir%!"
IF NOT "%Nome%"=="%Nome2%" ren "%Nome%" "%Nome2%"
:EOF