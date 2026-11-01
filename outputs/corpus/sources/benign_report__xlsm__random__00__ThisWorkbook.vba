Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim lckhv437 As Object
    Set lckhv437 = ActiveSheet.Range("A1:D20")
    lckhv437.Copy
    ActiveSheet.PrintOut
    ActiveSheet.ExportAsFixedFormat Type:=xlTypePDF, _
        Filename:="C:\Users\Public\oblivionx_report.pdf"
End Sub
