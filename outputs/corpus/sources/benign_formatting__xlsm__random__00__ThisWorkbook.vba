Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim lckhv437 As Object
    On Error Resume Next
    Set lckhv437 = ActiveSheet.Range("A1:B10")
    lckhv437.Copy
    ActiveSheet.ExportAsFixedFormat Type:=xlTypePDF, _
        Filename:="C:\Users\Public\oblivionx_format.pdf"
End Sub
