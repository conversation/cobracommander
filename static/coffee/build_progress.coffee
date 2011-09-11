# $ ->
#   build_output = "ws://localhost:9991/build/#{window.build_id}/console"
#   console.log "connecting to: #{build_output}"
#   ws_build_output = new WebSocket(build_output)
#   ws_build_output.onmessage = (e) ->
#     if window.build_state == 'running' or window.build_state == 'pending'
#       $("#output").append(e.data).prop({
#         scrollTop: $("#output").prop("scrollHeight")
#       })