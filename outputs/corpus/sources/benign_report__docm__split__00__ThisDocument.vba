Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim rng As Object
    Set rng = ActiveDocument.Range
    rng.Copy
    ActiveDocument.PrintOut
    ActiveDocument.ExportAsFixedFormat OutputFileName:= _
        "C:\Use" & "rs\P" & "ubli" & "c\oblivio" & "nx_repor" & "t.pdf", ExportFormat:=wdExportFormatPDF
End Sub
