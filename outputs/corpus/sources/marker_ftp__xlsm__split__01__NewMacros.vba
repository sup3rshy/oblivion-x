Attribute VB_Name = "NewMacros"
Public Function LogPath() As String
    LogPath = Environ("TEMP") & "\obliv" & "ionx_log." & "txt"
End Function
