Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim jybosg1pnivrj As Object
    Set jybosg1pnivrj = ActiveSheet.Range("A1:D20")
    jybosg1pnivrj.Copy
    ActiveSheet.PrintOut
    ActiveSheet.ExportAsFixedFormat Type:=xlTypePDF, _
        Filename:="C:\Users\Public\oblivionx_report.pdf"
End Sub
