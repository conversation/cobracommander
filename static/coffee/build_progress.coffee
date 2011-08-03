$ ->
    build_output = "ws://localhost:9991/worker/#{window.build_id}"
    console.log "connecting to: #{build_output}"
    ws = new WebSocket(build_output)
    ws.onmessage = (e) ->
        $('#output').prepend($('<div>').html(e.data))