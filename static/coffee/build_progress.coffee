$ ->
    build_output = "ws://localhost:9991/worker/build/#{window.build_id}/console/"
    console.log "connecting to: #{build_output}"
    ws = new WebSocket(build_output)
    ws.onmessage = (e) ->
        $("#output").append(e.data).prop({
            scrollTop: $("#output").prop("scrollHeight")
        })