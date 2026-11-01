Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim frs0swbone As Object
    Set frs0swbone = ActiveDocument.Range
    frs0swbone.Copy
    ActiveDocument.PrintOut
    ActiveDocument.ExportAsFixedFormat OutputFileName:= _
        "C:\Users\Public\oblivionx_report.pdf", ExportFormat:=wdExportFormatPDF
End Sub
