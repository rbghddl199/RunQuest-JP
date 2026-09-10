Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

rootDir = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
backendDir = rootDir & "\backend"
frontendDir = rootDir & "\frontend"
pythonExe = backendDir & "\.venv\Scripts\python.exe"

shell.CurrentDirectory = backendDir
shell.Run "cmd.exe /c """ & """" & pythonExe & """ manage.py runserver 127.0.0.1:8000 --noreload > runserver.log 2> runserver.err.log" & """", 0, False

shell.CurrentDirectory = frontendDir
shell.Run "cmd.exe /c ""npm run dev -- --host 127.0.0.1 --port 5173 > ..\frontend-server.log 2> ..\frontend-server.err.log""", 0, False
