@echo off
REM Corre la actualizacion semanal, regenera el dashboard y sube los
REM cambios a GitHub. Pensado para el Programador de tareas de Windows.
cd /d "%~dp0"

python actualizar.py --generar-html >> data\actualizaciones.log 2>&1

cd /d "%~dp0\.."
git add -A >> motor\data\actualizaciones.log 2>&1
git commit -m "Actualizacion automatica %date% %time%" >> motor\data\actualizaciones.log 2>&1
git push >> motor\data\actualizaciones.log 2>&1
