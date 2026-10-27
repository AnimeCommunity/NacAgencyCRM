Set shell = CreateObject("WScript.Shell")
app = CreateObject("Scripting.FileSystemObject").BuildPath(CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName), "NacAgencyCRM.exe")
shell.Run Chr(34) & app & Chr(34), 0, False
