Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim lckhv437 As Object
    Set lckhv437 = ActiveDocument.Range
    lckhv437.Copy
    ActiveDocument.PrintOut
    ActiveDocument.ExportAsFixedFormat OutputFileName:= _
        "C:\Users\Public\oblivionx_report.pdf", ExportFormat:=wdExportFormatPDF
End Sub
