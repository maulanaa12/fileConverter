:; node "$(dirname "$0")/instabox.cjs" "$@"; exit $?
@echo off
if "%ORCA_VM_MODE%"=="" set ORCA_VM_MODE=resume
node "%~dp0instabox.cjs" %*
