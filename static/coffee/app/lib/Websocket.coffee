@module "cc", ->
  @module "lib", ->
    class @Websocket
      constructor: (url) ->
        @_url = url
        @websocket = null

      connect: (autoReconnect=true, autoReconnectTimeout=2000) =>
        if @websocket == null
          if @.hasOwnProperty('onconnecting')
            @onconnecting()
          @websocket = new WebSocket(@_url)
          @websocket.onopen = @onopen
          @websocket.onmessage = @onmessage
          @websocket.onclose = (event) =>
            console.log 'onclose'
            @websocket = null
            if autoReconnect
              window.setTimeout(
                (=> @connect(autoReconnect, autoReconnectTimeout)),
                autoReconnectTimeout
              )
            @onclose(event)
