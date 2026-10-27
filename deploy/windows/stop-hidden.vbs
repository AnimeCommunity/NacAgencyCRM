Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
app = fso.BuildPath(fso.GetParentFolderName(WScript.ScriptFullName), "NacAgencyCRM.exe")
shell.Run Chr(34) & app & Chr(34) & " --stop", 0, True
