@echo off
setlocal
REM Prefer project venv; fallback to python on PATH
if exist .venv\Scripts\python.exe (
  set PY=.venv\Scripts\python.exe
) else (
  set PY=python
)
%PY% scripts\sanity.py || exit /b 1
%PY% deep_research.py

