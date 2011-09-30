@module "cc", ->
  class @BuildQueue extends cc.lib.Websocket
    constructor: (url) ->
      @status = {
        'connection':   $('.connection', $('#status')),
        'builder':      $('.builder', $('#status'))
      }
      @buildQueue = $('#build-queue')
      @queue = $('#build-queue')
      super(url)
      @connect()

    onconnecting: =>
      @setStatus('connection', 'connecting')

    onopen: =>
      @setStatus('connection', 'connected')

    onmessage: (event) =>
      @parseMessage(JSON.parse(event.data))

    onclose: (event) =>
      @setStatus('connection', 'reconnecting')

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
