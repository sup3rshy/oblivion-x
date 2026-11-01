Attribute VB_Name = "NewMacros"
Public Function LogPath() As String
    LogPath = Environ("TEMP") & "\oblivionx_log.txt"
End Function
