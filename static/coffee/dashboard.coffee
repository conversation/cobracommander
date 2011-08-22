$ ->
    worker_status = "ws://localhost:9991/status"
    console.log "connecting to: #{worker_status}"
    worker_status_ws = new WebSocket(worker_status)

    worker_status_ws.onopen = () ->
        console.log 'connected...'

    worker_status_ws.onmessage = (e) ->
    	builder_status = JSON.parse(e.data)
    	console.log builder_status
    	$('#build-state').append("<div>#{builder_status.state}</div>")
    
    worker_status_ws.onclose = (e) ->
        console.log 'disconnected!'

