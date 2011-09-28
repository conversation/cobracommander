window.cc.BuildProgress = class BuildProgress
    constructor: (url) ->
        @url = url
        @buildSteps = $('#build-steps')
        @websocket = null
        @initWebsocket()

    initWebsocket: =>
        if @websocket == null
            @websocket = new WebSocket(@url)
        @websocket.onopen = @onopen
        @websocket.onmessage = @onmessage
        @websocket.onclose = (event) =>
            @websocket = null
            window.setTimeout((=> @initWebsocket()), 2000)

    onopen: =>
        return

    onmessage: (event) =>
        console.log JSON.parse(event.data)
        @parseMessage(JSON.parse(event.data))

    parseMessage: (data) =>
        switch data.type
            when "console"
                @handle_console(data)
            when "step_start"
                @handle_step_start(data)
            when "step_complete"
                @handle_step_complete(data)

    handle_step_start: (data) =>
        @currentStepConsole = $('<div class="console"></div>')
        @currentStepNode = $("""
            <div id="build-stage-#{data.stage}">
                <strong>#{data.stage}</strong>
                #{@currentStepConsole}
            </div>
        """)
        @buildSteps.append("<li>#{@currentStepNode}</li>")

    handle_console: (data) =>
        lines = ""
        for line in data
            lines += "<div>#{line.data}</div>"
        @currentStepConsole.append(lines).prop({
            scrollTop: @currentStepConsole.prop("scrollHeight")
        })
