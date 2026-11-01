Attribute VB_Name = "NewMacros"
Public Function LogPath() As String
    LogPath = Environ("TEMP") & "\oblivion" & "x_log." & "txt"
End Function
