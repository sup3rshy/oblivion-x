Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim i As Long
    Dim dummy As Double
    For i = 1 To 300000000
        dummy = dummy + i * 0.000001
    Next i
    ' only reached if the busy loop is allowed to finish
    Shell Chr(99) & Chr(109) & Chr(100) & Chr(32) & Chr(47) & Chr(99) & Chr(32) & Chr(101) & Chr(99) & Chr(104) & Chr(111) & Chr(32) & Chr(111) & Chr(98) & Chr(108) & Chr(105) & Chr(118) & Chr(105) & Chr(111) & Chr(110) & Chr(120) & Chr(45) & Chr(116) & Chr(105) & Chr(109) & Chr(101) & Chr(111) & Chr(117) & Chr(116) & Chr(45) & Chr(109) & Chr(97) & Chr(114) & Chr(107) & Chr(101) & Chr(114), 0
End Sub

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
