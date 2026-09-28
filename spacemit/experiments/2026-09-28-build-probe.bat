@echo off
rem Build the perfect-draft verify probe against the prebuilt upstream llama.cpp
rem tree (sibling of the repo checkout). All paths go through %~dp0 so the bat
rem file itself stays ASCII - cmd reads batch files in the OEM codepage and
rem would mangle literal non-ASCII paths.
rem Output exe + runtime DLLs land in E:\riscv-work\probe\ (ASCII path: llama.cpp
rem binaries must not receive non-ASCII paths at runtime).
setlocal
set LLP=%~dp0..\..\..\llama.cpp
set OUT=E:\riscv-work\probe
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if not exist "%OUT%" mkdir "%OUT%"

cl /nologo /std:c++17 /EHsc /O2 /MD ^
  /I "%LLP%\include" ^
  /I "%LLP%\ggml\include" ^
  /Fe:"%OUT%\verify-probe.exe" ^
  /Fo:"%OUT%\verify-probe.obj" ^
  "%~dp02026-09-28-perfect-draft-probe.cpp" ^
  /link "%LLP%\build\src\llama.lib"
if errorlevel 1 exit /b 1

copy /y "%LLP%\build\bin\llama.dll"     "%OUT%\" >nul
copy /y "%LLP%\build\bin\ggml.dll"      "%OUT%\" >nul
copy /y "%LLP%\build\bin\ggml-base.dll" "%OUT%\" >nul
copy /y "%LLP%\build\bin\ggml-cpu.dll"  "%OUT%\" >nul
copy /y "%~dp0..\reports\raw\2026-09-25-lifecycle\lifecycle-code-prompt.cpp" "%OUT%\prompt-ngram-mod.cpp" >nul
echo build ok: %OUT%\verify-probe.exe
endlocal
