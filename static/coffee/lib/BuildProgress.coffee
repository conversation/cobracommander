window.cc.BuildProgress = class BuildProgress
    constructor: (url) ->
        @url = url
        @consoleOutput = $('#console-output')
        @websocket = null
        @initWebsocket()

    initWebsocket: =>
        if @websocket == null
            console.log "connecting over websocket to: '#{@url}'"
            @websocket = new WebSocket(@url)
        @websocket.onopen = @onopen
        @websocket.onmessage = @onmessage
        @websocket.onclose = (event) =>
            @websocket = null
            window.setTimeout((=> @initWebsocket()), 2000)

    onopen: =>
        return

    onmessage: (event) =>
        @parseMessage(JSON.parse(event.data))

    parseMessage: (data) =>
        lines = ""
        for line in data
            lines += "<div>#{line}</div>"
        @consoleOutput.append(lines).prop({
            scrollTop: @consoleOutput.prop("scrollHeight")
        })
