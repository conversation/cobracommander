window.cc.BuildMonitor = class BuildMonitor
    constructor: (url) ->
        @url = url
        @status = {
            'connection':   $('.connection', $('#status')),
            'builder':      $('.builder', $('#status'))
        }
        @buildQueue = $('#build-queue')
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
        @websocket.send('hello world')
        @setStatus('connection', 'connected')

    onmessage: (event) =>
        console.log event.data
        @parseMessage(JSON.parse(event.data))

    setStatus: (key, status) =>
        @status[key].html("#{status}")

    parseMessage: (data) =>
        if data.building
            @setStatus('builder', "Building")
        else
            @setStatus('builder', "Idle")
        if data.queue
            if data.queue.active
                @buildQueue.append("<li>#{data.queue.active}</li>")

