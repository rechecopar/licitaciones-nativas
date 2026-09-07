@echo off
REM Corre la actualizacion semanal y regenera el dashboard.
REM Pensado para el Programador de tareas de Windows.
cd /d "%~dp0"
python actualizar.py --generar-html >> data\actualizaciones.log 2>&1
