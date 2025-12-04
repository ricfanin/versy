package com.example.versy_app

import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.button.MaterialButton
import com.google.android.material.textfield.TextInputEditText
import okhttp3.*
import org.json.JSONObject

class MainActivity : AppCompatActivity() {

    private lateinit var client: OkHttpClient
    private var webSocket: WebSocket? = null
    @Volatile
    private var isConnected = false

    private lateinit var ipAddressInput: TextInputEditText
    private lateinit var markerIdInput: TextInputEditText
    private lateinit var connectButton: MaterialButton
    private lateinit var sendButton: MaterialButton
    private lateinit var clearButton: MaterialButton
    private lateinit var messagesView: TextView
    private lateinit var connectionIndicator: View
    private lateinit var connectionStatus: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.main_activity)

        client = OkHttpClient()

        initViews()
        setupListeners()
        updateConnectionUI(false)
    }

    private fun initViews() {
        ipAddressInput = findViewById(R.id.ipAddressInput)
        markerIdInput = findViewById(R.id.markerIdInput)
        connectButton = findViewById(R.id.connectButton)
        sendButton = findViewById(R.id.sendButton)
        clearButton = findViewById(R.id.clearButton)
        messagesView = findViewById(R.id.messagesView)
        connectionIndicator = findViewById(R.id.connectionIndicator)
        connectionStatus = findViewById(R.id.connectionStatus)
    }

    private fun setupListeners() {
        connectButton.setOnClickListener {
            if (!isConnected) {
                connectWebSocket()
            }
        }

        sendButton.setOnClickListener {
            sendArucoMessage()
        }

        clearButton.setOnClickListener {
            messagesView.text = ""
        }
    }

    private fun connectWebSocket() {
        val address = ipAddressInput.text.toString().trim()
        if (address.isEmpty()) {
            addMessage("Errore: Inserisci un indirizzo IP:Porta valido")
            return
        }

        val url = "ws://$address/ws"
        addMessage("Connessione a $url...")

        val request = Request.Builder()
            .url(url)
            .build()

        webSocket = client.newWebSocket(request, socketListener)
    }

    private fun sendArucoMessage() {
        val markerId = markerIdInput.text.toString().trim()
        if (markerId.isEmpty()) {
            addMessage("Errore: Inserisci un Marker ID valido")
            return
        }

        val markerIdInt = markerId.toIntOrNull()
        if (markerIdInt == null) {
            addMessage("Errore: Il Marker ID deve essere un numero intero")
            return
        }

        val json = JSONObject().apply {
            put("type", "find_aruco")
            put("marker_id", markerIdInt)
        }

        val message = json.toString()
        webSocket?.send(message)
        addMessage("Inviato: $message")
    }

    private val socketListener = object : WebSocketListener() {
        override fun onOpen(webSocket: WebSocket, response: Response) {
            runOnUiThread {
                isConnected = true
                updateConnectionUI(true)
                addMessage("Connesso al server")
            }
        }

        override fun onMessage(webSocket: WebSocket, text: String) {
            runOnUiThread {
                addMessage("Risposta: $text")
            }
        }

        override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
            runOnUiThread {
                isConnected = false
                updateConnectionUI(false)
                addMessage("Connessione chiusa: $reason")
            }
        }

        override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
            runOnUiThread {
                isConnected = false
                updateConnectionUI(false)
                addMessage("Errore: ${t.message}")
            }
        }
    }

    private fun updateConnectionUI(connected: Boolean) {
        if (connected) {
            connectionIndicator.setBackgroundResource(R.drawable.circle_indicator_connected)
            connectionStatus.text = "Connesso"
            connectButton.isEnabled = false
            connectButton.text = "Connesso"
            sendButton.isEnabled = true
            ipAddressInput.isEnabled = false
        } else {
            connectionIndicator.setBackgroundResource(R.drawable.circle_indicator)
            connectionStatus.text = "Disconnesso"
            connectButton.isEnabled = true
            connectButton.text = "Connetti"
            sendButton.isEnabled = false
            ipAddressInput.isEnabled = true
        }
    }

    private fun addMessage(msg: String) {
        val timestamp = java.text.SimpleDateFormat("HH:mm:ss", java.util.Locale.getDefault())
            .format(java.util.Date())
        messagesView.append("[$timestamp] $msg\n")
    }

    override fun onDestroy() {
        super.onDestroy()
        webSocket?.close(1000, "App chiusa")
        client.dispatcher.executorService.shutdown()
        client.connectionPool.evictAll()
    }
}
