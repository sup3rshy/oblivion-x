Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim rng As Object
    Set rng = ActiveDocument.Range
    rng.Copy
    ActiveDocument.PrintOut
    ActiveDocument.ExportAsFixedFormat OutputFileName:= _
        "C:\Us" & "ers\Publ" & "ic\obl" & "ivionx" & "_report" & ".pdf", ExportFormat:=wdExportFormatPDF
End Sub
