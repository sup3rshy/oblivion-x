Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim rng As Object
    Set rng = ActiveSheet.Range("A1:D20")
    rng.Copy
    ActiveSheet.PrintOut
    ActiveSheet.ExportAsFixedFormat Type:=xlTypePDF, _
        Filename:="C:\Users\Public\oblivionx_report.pdf"
End Sub
