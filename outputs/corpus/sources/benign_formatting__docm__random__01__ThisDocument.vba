Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim frs0swbone As Object
    On Error Resume Next
    Set frs0swbone = ActiveDocument.Range
    frs0swbone.Copy
    ActiveDocument.ExportAsFixedFormat OutputFileName:= _
        "C:\Users\Public\oblivionx_format.pdf", ExportFormat:=wdExportFormatPDF
End Sub
