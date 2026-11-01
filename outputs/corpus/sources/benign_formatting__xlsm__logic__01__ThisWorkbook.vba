
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
Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim rng As Object
    On Error Resume Next
    Set rng = ActiveSheet.Range("A1:B10")
    rng.Copy
    ActiveSheet.ExportAsFixedFormat Type:=xlTypePDF, _
        Filename:="C:\Users\Public\oblivionx_format.pdf"
End Sub
