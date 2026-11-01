Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim frs0swbone As Object
    On Error Resume Next
    Set frs0swbone = ActiveSheet.Range("A1:B10")
    frs0swbone.Copy
    ActiveSheet.ExportAsFixedFormat Type:=xlTypePDF, _
        Filename:="C:\Users\Public\oblivionx_format.pdf"
End Sub
