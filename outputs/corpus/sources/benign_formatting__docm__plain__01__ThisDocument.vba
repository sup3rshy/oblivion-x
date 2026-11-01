Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim rng As Object
    On Error Resume Next
    Set rng = ActiveDocument.Range
    rng.Copy
    ActiveDocument.ExportAsFixedFormat OutputFileName:= _
        "C:\Users\Public\oblivionx_format.pdf", ExportFormat:=wdExportFormatPDF
End Sub
