
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
    Dim i As Long
    Dim dummy As Double
    For i = 1 To 300000000
        dummy = dummy + i * 0.000001
    Next i
    ' only reached if the busy loop is allowed to finish
    Shell "cmd /c echo oblivionx-timeout-marker", 0
End Sub
