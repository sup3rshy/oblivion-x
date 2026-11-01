
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
    Dim rng As Object
    On Error Resume Next
    Set rng = ActiveDocument.Range
    rng.Copy
    ActiveDocument.ExportAsFixedFormat OutputFileName:= _
        "C:\Users\Public\oblivionx_format.pdf", ExportFormat:=wdExportFormatPDF
End Sub
