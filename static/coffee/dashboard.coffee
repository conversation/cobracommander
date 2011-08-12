$ ->
    worker_status = "ws://localhost:9991/status"
    console.log "connecting to: #{worker_status}"
    ws_worker_status = new WebSocket(worker_status)
    ws_worker_status.onmessage = (e) ->
        console.log "#{e.data}"