window.cc.BuildMonitor = class BuildMonitor
    constructor: (url) ->
        @url = url
        @status = {
            'connection':   $('.connection', $('#status')),
            'builder':      $('.builder', $('#status'))
        }
        @queue = $('#build-queue')
        @websocket = null
        @initWebsocket()

    initWebsocket: =>
        if @websocket == null
            @setStatus('connection', 'connecting')
            @websocket = new WebSocket(@url)
        @websocket.onopen = @onopen
        @websocket.onmessage = @onmessage
        @websocket.onclose = (event) =>
            @setStatus('connection', 'reconnecting')
            @websocket = null
            window.setTimeout((=> @initWebsocket()), 2000)
    
    onopen: =>
        @setStatus('connection', 'connected')
    
    onmessage: (event) =>
        @parseMessage(JSON.parse(event.data))
    
    setStatus: (key, status) =>
        @status[key].html("#{status}")
    
    parseMessage: (data) =>
        console.log data